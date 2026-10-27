import base64,hashlib,io,json,os,re,sqlite3,tempfile,time
from datetime import date
from pathlib import Path
from unittest.mock import patch
from django.test import TestCase,override_settings
from django.core import mail as django_mail
from django.core.management import call_command
from django.contrib.auth.hashers import check_password
from rest_framework.test import APIClient
from PIL import Image
from . import models as m
from .authentication import LegacyScryptHasher

def client():
    c=APIClient(enforce_csrf_checks=True);token=c.get('/api/csrf').json()['csrf_token'];c.credentials(HTTP_X_CSRFTOKEN=token,HTTP_ORIGIN='http://localhost:5173');return c
def signup(c,name='test_member'):
    response=c.post('/api/auth/signup',{'username':name,'password':'test-password-123','email':name.replace('_','')+'@gmail.com','birth_date':'1995-06-15','country':'IN'},format='json')
    assert response.status_code==201,response.content
    return response.json()
def viewing(c,public=True,rating=4,movie_id=1):
    r=c.post('/api/diary',{'movie':{'id':movie_id,'title':'Test film'},'rating':rating,'review':'A thoughtful review','watched_on':date.today().isoformat(),'is_public':public},format='json');assert r.status_code==201,r.content;return r.json()

class ApiTests(TestCase):
    def setUp(self):
        from django.core.cache import cache
        cache.clear();self.a=client();self.b=client()
    def test_health_and_csrf(self):
        self.assertEqual(self.a.get('/api/health').json()['backend'],'django')
        raw=APIClient(enforce_csrf_checks=True)
        self.assertEqual(raw.post('/api/auth/login',{'username':'test','password':'anything'},format='json').status_code,403)
        token=self.a.get('/api/csrf').json()['csrf_token'];self.a.credentials(HTTP_X_CSRFTOKEN=token,HTTP_ORIGIN='https://evil.example')
        self.assertEqual(self.a.post('/api/auth/login',{'username':'test','password':'anything'},format='json').status_code,403)
    def test_signup_validation_and_private_fields(self):
        self.assertEqual(self.a.post('/api/auth/signup',{'username':'bad','password':'password-123','country':'IN'},format='json').status_code,422)
        data=signup(self.a);self.assertNotIn('email',data);self.assertNotIn('birth_date',data)
        self.assertEqual(self.b.get('/api/auth/me').status_code,401)
        for url in ('/api/auth/me','/api/profiles/test_member','/api/profiles/test_member/details'):
            result=self.a.get(url).json();self.assertNotIn('email',result);self.assertNotIn('birth_date',result)
        self.assertEqual(self.b.post('/api/auth/signup',{'username':'test_member','password':'password-123','country':'IN','email':'testmember@gmail.com','birth_date':'1990-01-01'},format='json').status_code,409)
    def test_login_logout_and_profile(self):
        signup(self.a)
        self.assertEqual(self.a.patch('/api/profiles/me',{'display_name':'Film fan','bio':'My films','country':'JP'},format='json').json()['country'],'JP')
        self.a.post('/api/auth/logout',{},format='json');self.assertEqual(self.a.get('/api/auth/me').status_code,401)
        self.assertEqual(self.a.post('/api/auth/login',{'username':'test_member','password':'wrong-password'},format='json').status_code,401)
        self.assertEqual(self.a.post('/api/auth/login',{'username':'test_member','password':'test-password-123'},format='json').json()['display_name'],'Film fan')
    def test_watchlist_and_atomic_diary(self):
        signup(self.a);self.a.post('/api/watchlist',{'id':1,'title':'Film'},format='json');self.a.post('/api/watchlist',{'id':1,'title':'Film'},format='json')
        self.assertEqual(len(self.a.get('/api/watchlist').json()),1)
        data={'movie':{'id':1,'title':'Film'},'watched_on':date.today().isoformat(),'rating':4.5,'remove_from_watchlist':True}
        self.assertEqual(self.a.post('/api/diary',data,format='json').status_code,201);self.assertEqual(self.a.get('/api/watchlist').json(),[])
        self.assertEqual(self.b.get('/api/diary').status_code,401)
        self.assertEqual(self.a.post('/api/diary',{**data,'rating':4.2},format='json').status_code,422)
    def test_review_average_latest_public_rating(self):
        signup(self.a);signup(self.b,'other_member');viewing(self.a,rating=2);viewing(self.a,rating=4);viewing(self.a,False,rating=1);viewing(self.b,rating=5)
        scores=self.a.get('/api/movies/1/reviews').json();self.assertEqual(scores['rating_count'],2);self.assertEqual(scores['average_rating'],4.5)
        self.assertEqual(len(self.a.get('/api/diary').json()),3)
    def test_diary_owner_and_original_film(self):
        signup(self.a);signup(self.b,'another_member');entry=viewing(self.a)
        self.assertEqual(self.b.delete('/api/diary/'+str(entry['id'])).status_code,404)
        payload={'movie':{'id':2,'title':'Other film'},'watched_on':date.today().isoformat()}
        self.assertEqual(self.a.patch('/api/diary/'+str(entry['id']),payload,format='json').status_code,422)
    def test_private_list_order_and_public_sharing(self):
        signup(self.a);signup(self.b,'list_reader');lid=self.a.post('/api/lists',{'name':'Favorites'},format='json').json()['id'];url=f'/api/lists/{lid}'
        self.assertEqual(self.b.get(url).status_code,404)
        for id in (1,2,1):self.a.post(url+'/movies',{'id':id,'title':str(id)},format='json')
        self.a.patch(url+'/movies/2',{'direction':'up'},format='json');self.assertEqual(self.a.get(url).json()['movies'][0]['id'],2)
        self.assertEqual(self.b.post(url+'/movies',{'id':3,'title':'No'},format='json').status_code,404)
        self.a.patch(url,{'name':'Favorites','is_public':True},format='json');self.assertFalse(self.b.get(url).json()['is_owner'])
        self.assertEqual(self.b.get('/api/profiles/test_member/lists').json()[0]['movie_count'],2)
    def test_likes_comments_and_deletion(self):
        signup(self.a);signup(self.b,'review_reader');private=viewing(self.a,False);entry=viewing(self.a);url=f"/api/reviews/{entry['id']}"
        self.assertEqual(self.b.post(f"/api/reviews/{private['id']}/like",{},format='json').status_code,404)
        for _ in range(2):self.b.post(url+'/like',{},format='json')
        self.assertEqual(self.b.get(url+'/reactions').json()['likes'],1)
        cid=self.b.post(url+'/comments',{'body':'Thoughtful comment','spoilers':True},format='json').json()['id']
        self.assertEqual(self.a.delete(url+f'/comments/{cid}').status_code,404)
        self.assertTrue(self.b.get(url+'/comments').json()['results'][0]['is_owner'])
        self.a.delete('/api/diary/'+str(entry['id']));self.assertEqual(m.ReviewLike.objects.count(),0);self.assertEqual(m.ReviewComment.objects.count(),0)
    def test_follow_feed_privacy_and_people(self):
        signup(self.a);signup(self.b,'feed_reader');viewing(self.a);viewing(self.a,False)
        self.b.post('/api/profiles/test_member/follow',{},format='json');result=self.b.get('/api/feed').json()['results'];self.assertEqual(len(result),1);self.assertNotIn('watched_on',result[0])
        self.assertEqual(self.a.get('/api/profiles/test_member/people').json()['results'][0]['username'],'feed_reader')
        self.a.patch('/api/profile/details',{'show_activity':False},format='json');self.assertEqual(self.b.get('/api/feed').json()['results'],[])
        self.assertEqual(self.b.get('/api/profiles/test_member/activity').json()['results'],[])
    def test_favorite_five_and_visitor_privacy(self):
        signup(self.a);slots=[None,{'id':1,'title':'Film'},None,None,{'id':2,'title':'Other'}]
        self.assertEqual(self.a.put('/api/profile/favorites',{'movies':slots},format='json').status_code,200)
        self.assertEqual(self.a.put('/api/profile/favorites',{'movies':[None]*6},format='json').status_code,422)
        self.a.patch('/api/profile/details',{'show_favorites':False},format='json')
        self.assertEqual(self.a.get('/api/profiles/test_member/details').json()['favorite_slots'][4]['id'],2)
        self.assertEqual(self.b.get('/api/profiles/test_member/details').json()['favorite_slots'],[None]*5)
        self.assertEqual(self.a.get('/api/profiles/test_member/details?visitor=true').json()['favorite_slots'],[None]*5)
    def test_pins_and_public_stats(self):
        signup(self.a);private=viewing(self.a,False);entry=viewing(self.a)
        self.assertEqual(self.a.patch('/api/profile/details',{'pinned_review':private['id']},format='json').status_code,422)
        self.a.patch('/api/profile/details',{'pinned_review':entry['id'],'show_stats':True},format='json')
        detail=self.b.get('/api/profiles/test_member/details').json();self.assertEqual(detail['public_stats']['rated_viewings'],1);self.assertEqual(detail['pinned_review']['id'],entry['id'])
        self.a.delete('/api/diary/'+str(entry['id']));self.assertIsNone(self.b.get('/api/profiles/test_member/details').json()['pinned_review'])
    def test_upload_validation_and_private_images(self):
        signup(self.a);self.assertEqual(self.a.put('/api/profile/images/avatar',{'data':base64.b64encode(b'<svg/>').decode()},format='json').status_code,422)
        out=io.BytesIO();Image.new('RGB',(60,40),'orange').save(out,'PNG')
        self.assertEqual(self.a.put('/api/profile/images/avatar',{'data':base64.b64encode(out.getvalue()).decode()},format='json').status_code,200)
        response=self.b.get('/api/profiles/test_member/images/avatar');self.assertEqual(response['Content-Type'],'image/webp')
        with Image.open(io.BytesIO(response.content)) as im:self.assertEqual(im.size,(400,400))
    def test_block_and_reports(self):
        signup(self.a);signup(self.b,'blocked_member');entry=viewing(self.a);self.b.post('/api/profiles/test_member/follow',{},format='json');self.a.post('/api/profiles/blocked_member/block',{},format='json')
        self.assertEqual(self.b.post('/api/profiles/test_member/follow',{},format='json').status_code,403)
        self.assertEqual(self.b.post(f"/api/reviews/{entry['id']}/like",{},format='json').status_code,403)
        self.assertEqual(self.b.post('/api/profiles/test_member/report',{'reason':'A reason to review this account'},format='json').status_code,201)
    def test_stats_preferences_and_account_delete_cascades(self):
        signup(self.a);viewing(self.a);viewing(self.a)
        stats=self.a.get('/api/stats').json();self.assertEqual(stats['viewings'],2);self.assertEqual(stats['rewatches'],1)
        self.a.patch('/api/preferences',{'hide_spoilers':False},format='json');self.assertFalse(self.a.get('/api/preferences').json()['hide_spoilers'])
        self.assertEqual(self.a.delete('/api/account',{'confirmation':'test_member','current_password':'test-password-123'},format='json').status_code,204)
        self.assertEqual(m.User.objects.count(),0);self.assertEqual(m.Diary.objects.count(),0);self.assertEqual(m.ApiSession.objects.count(),0)
    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',EMAIL_HOST='smtp.example.test',DEFAULT_FROM_EMAIL='frame@example.test')
    @patch.dict(os.environ,{'APP_PUBLIC_URL':'https://frame.example.test'})
    def test_verification_recovery_and_single_use(self):
        signup(self.a);self.assertEqual(len(django_mail.outbox),1);verification=re.search(r'token=([A-Za-z0-9_-]+)',django_mail.outbox[0].body)[1]
        self.assertEqual(self.a.post('/api/account/verification/send',{},format='json').status_code,429)
        self.assertEqual(self.a.post('/api/auth/email/verify',{'token':verification},format='json').status_code,200)
        self.assertEqual(self.a.post('/api/auth/email/verify',{'token':verification},format='json').status_code,400)
        self.assertTrue(self.a.get('/api/account').json()['email_verified'])
        self.a.post('/api/auth/password-reset/request',{'email':'testmember@gmail.com'},format='json');reset=re.search(r'token=([A-Za-z0-9_-]+)',django_mail.outbox[-1].body)[1]
        self.assertEqual(self.a.post('/api/auth/password-reset/confirm',{'token':reset,'new_password':'new-password-123'},format='json').status_code,200)
        self.assertEqual(self.a.get('/api/auth/me').status_code,401)
        self.assertEqual(self.a.post('/api/auth/password-reset/confirm',{'token':reset,'new_password':'new-password-123'},format='json').status_code,400)
        self.assertEqual(self.a.post('/api/auth/login',{'username':'test_member','password':'new-password-123'},format='json').status_code,200)
    @patch('core.movies.tmdb')
    def test_movie_search_country_and_providers(self,tmdb):
        tmdb.return_value={'results':[{'id':1,'title':'Film','genre_ids':[18],'original_language':'en'}],'total_pages':1}
        self.assertEqual(self.a.get('/api/movies/search?query=Film&genre=18').status_code,200)
        self.assertEqual(self.a.get('/api/movies/search?language=invalid').status_code,422)
        self.assertEqual(self.a.get('/api/movies/country').status_code,401)
        signup(self.a);self.a.get('/api/movies/country');self.assertEqual(tmdb.call_args.kwargs['with_origin_country'],'IN')
        tmdb.return_value={'results':{'IN':{'flatrate':[{'provider_id':1,'provider_name':'Example'}],'link':'https://www.themoviedb.org/movie/1/watch'}}}
        self.assertEqual(self.a.get('/api/movies/1/watch-providers').json()['flatrate'][0]['provider_id'],1)
    def test_django_admin_requires_staff(self):
        response=self.a.get('/admin/');self.assertEqual(response.status_code,302)
        signup(self.a);self.assertEqual(self.a.get('/admin/').status_code,302)

class MigrationTests(TestCase):
    def test_preserves_legacy_hash_sessions_ids_and_movie_data(self):
        from django.core.cache import cache
        cache.clear()
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'legacy.db';salt='12'*16;password='legacy-password';encoded=hashlib.scrypt(password.encode(),salt=bytes.fromhex(salt),n=16384,r=8,p=1).hex();raw_token='legacy-test-session'
            with sqlite3.connect(path) as db:
                db.execute('CREATE TABLE users(id INTEGER PRIMARY KEY,username TEXT,password_hash TEXT,display_name TEXT,bio TEXT,country TEXT)');db.execute('INSERT INTO users VALUES (42,?,?,?,?,?)',('legacy_viewer',salt+':'+encoded,'Legacy','Bio','IN'))
                db.execute('CREATE TABLE sessions(token_hash TEXT PRIMARY KEY,user_id INTEGER,expires INTEGER)');db.execute('INSERT INTO sessions VALUES (?,?,?)',(hashlib.sha256(raw_token.encode()).hexdigest(),42,int(time.time())+600))
                db.execute('CREATE TABLE watchlist(user_id INTEGER,movie_id INTEGER,movie TEXT)');db.execute('INSERT INTO watchlist VALUES (?,?,?)',(42,1,json.dumps({'id':1,'title':'Imported film'})))
            db.close()
            original=path.read_bytes();call_command('import_legacy',source=str(path),no_backup=True,stdout=io.StringIO())
            self.assertEqual(path.read_bytes(),original);user=m.User.objects.get(pk=42);self.assertTrue(check_password(password,user.password));self.assertTrue(user.password.startswith('frame_scrypt$'))
            c=client();c.cookies['frame_session']=raw_token;self.assertEqual(c.get('/api/auth/me').json()['id'],42);self.assertEqual(c.get('/api/watchlist').json()[0]['title'],'Imported film')
            self.assertEqual(c.post('/api/auth/login',{'username':'legacy_viewer','password':password},format='json').status_code,200);user.refresh_from_db();self.assertTrue(user.password.startswith('pbkdf2_sha256$'))
            call_command('import_legacy',source=str(path),no_backup=True,stdout=io.StringIO());self.assertEqual(m.User.objects.count(),1)
