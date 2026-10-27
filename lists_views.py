from django.db import transaction
from django.db.models import Count,Max
from rest_framework.response import Response
from .models import FilmList,ListItem
from .common import endpoint,required,parse,Problem
from . import schemas

def list_data(row):return {key:getattr(row,key) for key in ('id','user_id','name','description','is_public','created_at')}
def owned(request,list_id):
    row=FilmList.objects.filter(id=list_id,user=required(request)).first()
    if not row:raise Problem(404,'List not found.')
    return row

@endpoint('GET','POST')
def lists(request):
    user=required(request)
    if request.method=='GET':return Response([{**list_data(row),'movie_count':row.movie_count} for row in FilmList.objects.filter(user=user).annotate(movie_count=Count('items')).order_by('-id')])
    data=parse(schemas.ListData,request.data)
    if not data.name.strip():raise Problem(422,'Give your list a name.')
    row=FilmList.objects.create(user=user,name=data.name.strip(),description=data.description.strip(),is_public=data.is_public)
    return Response(list_data(row),status=201)

@endpoint('GET','PATCH','DELETE')
def detail(request,list_id):
    if request.method=='GET':
        row=FilmList.objects.select_related('user').filter(pk=list_id).first();own=bool(row and request.user.is_authenticated and row.user_id==request.user.id)
        if not row or not (own or row.is_public):raise Problem(404,'List not found.')
        return Response({**list_data(row),'username':row.user.username,'display_name':row.user.display_name,'is_owner':own,'movies':list(row.items.order_by('position','movie_id').values_list('movie',flat=True))})
    row=owned(request,list_id)
    if request.method=='DELETE':row.delete();return Response(status=204)
    data=parse(schemas.ListData,request.data)
    if not data.name.strip():raise Problem(422,'Give your list a name.')
    row.name=data.name.strip();row.description=data.description.strip();row.is_public=data.is_public;row.save();return Response({'message':'List updated.'})

@endpoint('POST')
def add_movie(request,list_id):
    data=parse(schemas.Movie,request.data)
    with transaction.atomic():
        row=owned(request,list_id);FilmList.objects.select_for_update().get(pk=row.pk)
        position=(row.items.aggregate(value=Max('position'))['value'] or 0)+1
        ListItem.objects.get_or_create(film_list=row,movie_id=data.id,defaults={'movie':data.model_dump(mode='json'),'position':position})
    return Response({'message':'Film added to list.'},status=201)

@endpoint('PATCH','DELETE')
def list_movie(request,list_id,movie_id):
    with transaction.atomic():
        row=owned(request,list_id);FilmList.objects.select_for_update().get(pk=row.pk)
        if request.method=='DELETE':row.items.filter(movie_id=movie_id).delete();return Response(status=204)
        data=parse(schemas.MoveMovie,request.data);items=list(row.items.order_by('position','movie_id'));ids=[item.movie_id for item in items]
        if movie_id not in ids:raise Problem(404,'Film not found in list.')
        i=ids.index(movie_id);j=i+(-1 if data.direction=='up' else 1)
        if 0<=j<len(items):items[i],items[j]=items[j],items[i]
        for position,item in enumerate(items):item.position=position
        ListItem.objects.bulk_update(items,['position'])
    return Response({'message':'List order updated.'})
