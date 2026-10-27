import base64,io
from collections import Counter
from django.db import transaction
from django.db.models import Avg,Count
from django.http import HttpResponse
from django.utils import timezone
from rest_framework.response import Response
from .models import Diary,FilmList,Favorite,ProfileImage,ProfileDetails,Block
from .common import endpoint,required,parse,member,Problem,paginated
from .journal_views import latest_ratings
from . import schemas

def settings_for(user):return ProfileDetails.objects.filter(user=user).first() or ProfileDetails(user=user)

@endpoint('GET')
def profile(request,username):
    user=member(username);query=Diary.objects.filter(user=user,is_public=True)
    return Response({'id':user.id,'username':user.username,'display_name':user.display_name,'bio':user.bio,'stats':{'films_watched':query.values('movie_id').distinct().count(),'reviews_written':query.exclude(review='').count(),'public_viewings':query.count(),'average_rating':latest_ratings(query).aggregate(value=Avg('rating'))['value']}})

@endpoint('GET')
def activity(request,username):
    user=member(username);own=bool(request.user.is_authenticated and request.user.id==user.id and request.query_params.get('visitor')!='true')
    if not settings_for(user).show_activity and not own:return Response({'results':[],'total_pages':0,'page':1})
    rows,total,number=paginated(Diary.objects.filter(user=user,is_public=True).order_by('-id'),request)
    return Response({'page':number,'total_pages':total,'results':[{key:getattr(e,key) for key in ('id','movie','rating','review','spoilers','created_at')} for e in rows]})

@endpoint('GET')
def public_lists(request,username):
    user=member(username);rows=FilmList.objects.filter(user=user,is_public=True).annotate(movie_count=Count('items')).order_by('-id')
    return Response(list(rows.values('id','name','description','movie_count')))

@endpoint('GET')
def details(request,username):
    user=member(username);own=bool(request.user.is_authenticated and request.user.id==user.id and request.query_params.get('visitor')!='true');s=settings_for(user)
    slots=[None]*5
    if own or s.show_favorites:
        for row in Favorite.objects.filter(user=user).order_by('position'):slots[row.position]=row.movie
    images={row.kind:f'/api/profiles/{user.username}/images/{row.kind}?v={row.updated_at.isoformat()}' for row in ProfileImage.objects.filter(user=user)}
    pinned_review=Diary.objects.filter(pk=s.pinned_review_id,user=user,is_public=True).first()
    pinned_list=FilmList.objects.filter(pk=s.pinned_list_id,user=user,is_public=True).first()
    public_stats=None
    if own or s.show_stats:
        rated=list(Diary.objects.filter(user=user,is_public=True,rating__isnull=False).values_list('rating',flat=True));public_stats={'ratings':dict(Counter(str(r) for r in rated)),'rated_viewings':len(rated)}
    return Response({'is_owner':own,'genres':s.genres,'favorites':[m for m in slots if m],'favorite_slots':slots,'images':images,'show_favorites':s.show_favorites,'show_activity':s.show_activity,'show_stats':s.show_stats,'public_stats':public_stats,'pinned_review':{key:getattr(pinned_review,key) for key in ('id','movie','rating','review','spoilers')} if pinned_review else None,'pinned_list':{key:getattr(pinned_list,key) for key in ('id','name','description')} if pinned_list else None,'blocked':bool(request.user.is_authenticated and Block.objects.filter(user=request.user,target=user).exists())})

@endpoint('PATCH')
def update_details(request):
    user=required(request);data=parse(schemas.ProfileDetails,request.data)
    if data.pinned_review and not Diary.objects.filter(pk=data.pinned_review,user=user,is_public=True).exclude(review='').exists():raise Problem(422,'Choose one of your public reviews.')
    if data.pinned_list and not FilmList.objects.filter(pk=data.pinned_list,user=user,is_public=True).exists():raise Problem(422,'Choose one of your public lists.')
    values=data.model_dump();values['pinned_review_id']=values.pop('pinned_review');values['pinned_list_id']=values.pop('pinned_list');values['genres']=values['genres'].strip()
    ProfileDetails.objects.update_or_create(user=user,defaults=values);return Response({'message':'Profile preferences saved.'})

@endpoint('PUT')
def favorites(request):
    user=required(request);data=parse(schemas.Favorites,request.data);selected=[m for m in data.movies if m]
    if len({m.id for m in selected})!=len(selected):raise Problem(422,'Choose five different films at most.')
    with transaction.atomic():
        Favorite.objects.filter(user=user).delete();Favorite.objects.bulk_create([Favorite(user=user,position=i,movie=m.model_dump(mode='json')) for i,m in enumerate(data.movies) if m])
    return Response({'message':'Favorite five saved.'})

@endpoint('PUT','DELETE')
def upload_image(request,kind):
    user=required(request)
    if kind not in ('avatar','banner'):raise Problem(422,'Choose avatar or banner.')
    if request.method=='DELETE':ProfileImage.objects.filter(user=user,kind=kind).delete();return Response(status=204)
    data=parse(schemas.ImageData,request.data)
    try:
        from PIL import Image,ImageOps
        raw=base64.b64decode(data.data,validate=True)
        if len(raw)>2*1024*1024:raise ValueError()
        with Image.open(io.BytesIO(raw)) as im:
            if im.format not in ('JPEG','PNG','WEBP') or im.width*im.height>20000000:raise ValueError()
            im=ImageOps.exif_transpose(im).convert('RGB');im=ImageOps.fit(im,(400,400) if kind=='avatar' else (1600,500));out=io.BytesIO();im.save(out,format='WEBP',quality=85)
    except Exception:raise Problem(422,'Use a valid JPG, PNG or WebP image under 2 MB and 20 megapixels.')
    ProfileImage.objects.update_or_create(user=user,kind=kind,defaults={'data':out.getvalue(),'updated_at':timezone.now()});return Response({'message':'Profile image saved.'})

@endpoint('GET')
def image(request,username,kind):
    row=ProfileImage.objects.filter(user=member(username),kind=kind).first()
    if not row:raise Problem(404,'Image not found.')
    return HttpResponse(bytes(row.data),content_type='image/webp',headers={'Cache-Control':'no-cache','X-Content-Type-Options':'nosniff'})
