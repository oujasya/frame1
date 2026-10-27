from django.db import transaction
from django.db.models import OuterRef,Subquery,Avg,Count
from django.utils import timezone
from rest_framework.response import Response
from .models import Watchlist,Diary
from .common import endpoint,required,parse,Problem,paginated,serialize_entry
from . import schemas

def latest_ratings(query):
    latest=Diary.objects.filter(user_id=OuterRef('user_id'),movie_id=OuterRef('movie_id'),is_public=True,rating__isnull=False).order_by('-id').values('id')[:1]
    return query.filter(is_public=True,rating__isnull=False,pk=Subquery(latest))

@endpoint('GET','POST')
def watchlist(request):
    user=required(request)
    if request.method=='GET':return Response(list(Watchlist.objects.filter(user=user).order_by('-id').values_list('movie',flat=True)))
    data=parse(schemas.Movie,request.data);Watchlist.objects.get_or_create(user=user,movie_id=data.id,defaults={'movie':data.model_dump(mode='json')})
    return Response(data.model_dump(mode='json'),status=201)

@endpoint('DELETE')
def remove_watchlist(request,movie_id):Watchlist.objects.filter(user=required(request),movie_id=movie_id).delete();return Response(status=204)

@endpoint('GET','POST')
def diary(request):
    user=required(request)
    if request.method=='GET':return Response([serialize_entry(e) for e in Diary.objects.filter(user=user).order_by('-watched_on','-id')])
    data=parse(schemas.Entry,request.data)
    with transaction.atomic():
        entry=Diary.objects.create(user=user,movie_id=data.movie.id,movie=data.movie.model_dump(mode='json'),rating=data.rating,review=data.review,watched_on=data.watched_on,spoilers=data.spoilers,is_public=data.is_public)
        if data.remove_from_watchlist:Watchlist.objects.filter(user=user,movie_id=data.movie.id).delete()
    return Response(serialize_entry(entry),status=201)

@endpoint('PATCH','DELETE')
def diary_entry(request,entry_id):
    entry=Diary.objects.filter(id=entry_id,user=required(request)).first()
    if not entry:raise Problem(404,'Diary entry not found.')
    if request.method=='DELETE':entry.delete();return Response(status=204)
    data=parse(schemas.Entry,request.data)
    if data.movie.id!=entry.movie_id:raise Problem(422,'A diary entry must keep its original film.')
    entry.movie=data.movie.model_dump(mode='json')
    for key in ('rating','review','watched_on','spoilers','is_public'):setattr(entry,key,getattr(data,key))
    entry.updated_at=timezone.now();entry.save();return Response(serialize_entry(entry))

@endpoint('GET')
def reviews(request,movie_id):
    if movie_id<1:raise Problem(422,'Invalid movie ID.')
    query=Diary.objects.filter(movie_id=movie_id,is_public=True)
    summary=latest_ratings(query).aggregate(rating_count=Count('id'),average_rating=Avg('rating'))
    review_query=query.exclude(review='').select_related('user').order_by('-id');entries,total,number=paginated(review_query,request)
    return Response({**summary,'review_count':review_query.count(),'page':number,'total_pages':total,'results':[{key:getattr(e,key) for key in ('id','user_id','rating','review','spoilers','created_at')}|{'username':e.user.username,'display_name':e.user.display_name} for e in entries]})
