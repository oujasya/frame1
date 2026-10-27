import json,sqlite3,time
from pathlib import Path
from datetime import datetime,timezone
from django.core.management.base import BaseCommand,CommandError
from django.core.management.color import no_style
from django.db import transaction,connection
from core import models as m

class Command(BaseCommand):
    help='Copy legacy FRAME SQLite records into Django, preserving IDs, credentials and sessions. Source is never edited.'
    def add_arguments(self,parser):parser.add_argument('--source',required=True);parser.add_argument('--no-backup',action='store_true')
    def handle(self,*args,**options):
        source=Path(options['source']).resolve()
        if not source.is_file():raise CommandError('Source database not found.')
        if connection.vendor=='sqlite' and source==Path(connection.settings_dict['NAME']).resolve():raise CommandError('Source and destination must be different databases.')
        if m.LegacyImport.objects.filter(source=str(source)).exists():self.stdout.write('Source already imported; no records changed.');return
        if m.User.objects.exists() or m.Diary.objects.exists() or m.FilmList.objects.exists():raise CommandError('Destination is not empty. Import into a fresh Django database.')
        legacy=sqlite3.connect(source.as_uri()+'?mode=ro',uri=True);legacy.row_factory=sqlite3.Row
        if not options['no_backup']:
            backup=source.with_name(source.stem+'-before-django-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'.db')
            with sqlite3.connect(backup) as target:legacy.backup(target)
        tables={r[0] for r in legacy.execute("SELECT name FROM sqlite_master WHERE type='table'")};counts={}
        def rows(table):
            result=[dict(row) for row in legacy.execute(f'SELECT * FROM "{table}" ORDER BY rowid')] if table in tables else []
            counts[table]=len(result);return result
        def insert(model,table,convert):
            for row in rows(table):model.objects.create(**convert(row))
        try:
            with transaction.atomic():
                for row in rows('users'):
                    password=row['password_hash']
                    if ':' in password:
                        salt,value=password.split(':',1);password=f'frame_scrypt${salt}${value}'
                    m.User.objects.create(id=row['id'],username=row['username'],password=password,display_name=row['display_name'],bio=row.get('bio',''),country=row.get('country'),birth_date=row.get('birth_date'),email=row.get('email'),recovery_email=row.get('recovery_email'),verified_recovery_email=row.get('verified_recovery_email'),hide_spoilers=bool(row.get('hide_spoilers',1)))
                insert(m.ApiSession,'sessions',lambda r:{k:r[k] for k in ('token_hash','user_id','expires')})
                insert(m.Watchlist,'watchlist',lambda r:{'user_id':r['user_id'],'movie_id':r['movie_id'],'movie':json.loads(r['movie'])})
                insert(m.Diary,'diary',lambda r:{**{k:r[k] for k in ('id','user_id','movie_id','rating','review','watched_on','created_at','updated_at')},'movie':json.loads(r['movie']),'spoilers':bool(r['spoilers']),'is_public':bool(r['is_public'])})
                insert(m.FilmList,'lists',lambda r:{**{k:r[k] for k in ('id','user_id','name','description','created_at')},'is_public':bool(r['is_public'])})
                insert(m.ListItem,'list_items',lambda r:{'film_list_id':r['list_id'],'movie_id':r['movie_id'],'movie':json.loads(r['movie']),'position':r['position']})
                insert(m.ReviewLike,'review_likes',lambda r:{'user_id':r['user_id'],'review_id':r['review_id']})
                insert(m.ReviewComment,'review_comments',lambda r:{**{k:r[k] for k in ('id','user_id','review_id','body','created_at')},'spoilers':bool(r['spoilers'])})
                insert(m.Follow,'follows',lambda r:{'follower_id':r['follower_id'],'followee_id':r['followee_id']})
                insert(m.Block,'blocks',lambda r:{'user_id':r['user_id'],'target_id':r['target_id']})
                insert(m.Report,'reports',lambda r:{k:r[k] for k in ('id','user_id','target_id','reason','created_at')})
                insert(m.ProfileDetails,'profile_details',lambda r:{'user_id':r['user_id'],'genres':r['genres'],'show_favorites':bool(r['show_favorites']),'show_activity':bool(r['show_activity']),'show_stats':bool(r['show_stats']),'pinned_review_id':r['pinned_review'],'pinned_list_id':r['pinned_list']})
                insert(m.Favorite,'profile_favorites',lambda r:{'user_id':r['user_id'],'position':r['position'],'movie':json.loads(r['movie'])})
                insert(m.ProfileImage,'profile_images',lambda r:{k:r[k] for k in ('user_id','kind','data','updated_at')})
                insert(m.PasswordReset,'password_resets',lambda r:{k:r[k] for k in ('token_hash','user_id','expires')})
                insert(m.EmailVerification,'email_verifications',lambda r:{k:r[k] for k in ('token_hash','user_id','email','expires')})
                insert(m.EmailSendLimit,'email_send_limits',lambda r:{k:r[k] for k in ('user_id','last_sent')})
                all_models=[m.User,m.Watchlist,m.Diary,m.FilmList,m.ListItem,m.ReviewLike,m.ReviewComment,m.Follow,m.Block,m.Report,m.Favorite,m.ProfileImage]
                with connection.cursor() as cursor:
                    for statement in connection.ops.sequence_reset_sql(no_style(),all_models):cursor.execute(statement)
                m.LegacyImport.objects.create(source=str(source),counts=counts)
        finally:legacy.close()
        self.stdout.write(self.style.SUCCESS('Legacy import complete: '+json.dumps(counts,sort_keys=True)))
