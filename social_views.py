from collections import Counter
from django.db import transaction
from django.db.models import Q
from rest_framework.response import Response
from .models import User,Diary,ReviewLike,ReviewComment,Follow,Block,Report,Favorite,ProfileDetails
from .common import endpoint,required,member,parse,Problem,paginated,serialize_entry
from . import schemas

def blocked(a,b):return Block.objects.filter(Q(user=a,target=b)|Q(user=b,target=a)).exists()
def review_item(review_id):
    entry=Diary.objects.filter(pk=review_id,is_public=True).exclude(review='').first()
    if not entry:raise Problem(404,'Public review not found.')
    return entry

@endpoint('GET')
def reactions(request,review_id):
    entry=review_item(review_id)
    return Response({'likes':entry.likes.count(),'comments':entry.comments.count(),'liked':bool(request.user.is_authenticated and entry.likes.filter(user=request.user).exists())})

@endpoint('POST','DELETE')
def like(request,review_id):
    user=required(request);entry=review_item(review_id)
    if request.method=='DELETE':entry.likes.filter(user=user).delete()
    else:
        if blocked(user,entry.user):raise Problem(403,'Interactions are unavailable between these members.')
        ReviewLike.objects.get_or_create(user=user,review=entry)
    return Response(status=204)

@endpoint('GET','POST')
def comments(request,review_id):
    entry=review_item(review_id)
    if request.method=='POST':
        user=required(request);data=parse(schemas.CommentData,request.data)
        if blocked(user,entry.user):raise Problem(403,'Interactions are unavailable between these members.')
        if not data.body.strip():raise Problem(422,'Write a comment first.')
        row=ReviewComment.objects.create(user=user,review=entry,body=data.body.strip(),spoilers=data.spoilers);return Response({'id':row.id},status=201)
    rows,total,_=paginated(entry.comments.select_related('user').order_by('id'),request)
    return Response({'total_pages':total,'results':[{key:getattr(row,key) for key in ('id','user_id','review_id','body','spoilers','created_at')}|{'username':row.user.username,'display_name':row.user.display_name,'is_owner':bool(request.user.is_authenticated and request.user.id==row.user_id)} for row in rows]})

@endpoint('DELETE')
def delete_comment(request,review_id,comment_id):
    review_item(review_id);deleted,_=ReviewComment.objects.filter(pk=comment_id,review_id=review_id,user=required(request)).delete()
    if not deleted:raise Problem(404,'Comment not found.')
    return Response(status=204)

@endpoint('GET')
def connections(request,username):
    target=member(username);user=request.user
    return Response({'followers':target.followers.count(),'following':target.following.count(),'followed':bool(user.is_authenticated and Follow.objects.filter(follower=user,followee=target).exists()),'is_self':bool(user.is_authenticated and user.id==target.id)})

@endpoint('POST','DELETE')
def follow(request,username):
    user=required(request);target=member(username)
    if request.method=='DELETE':Follow.objects.filter(follower=user,followee=target).delete()
    else:
        if user.id==target.id:raise Problem(422,'You cannot follow yourself.')
        if blocked(user,target):raise Problem(403,'Following is unavailable between these members.')
        Follow.objects.get_or_create(follower=user,followee=target)
    return Response(status=204)

@endpoint('GET')
def members(request):
    query=request.query_params.get('q','').strip()
    if not 2<=len(query)<=24:raise Problem(422,'Enter 2–24 characters.')
    return Response(list(User.objects.filter(Q(username__icontains=query)|Q(display_name__icontains=query),is_active=True).order_by('username').values('username','display_name','bio')[:20]))

@endpoint('GET')
def feed(request):
    user=required(request);ids=Follow.objects.filter(follower=user).values('followee_id')
    hidden=ProfileDetails.objects.filter(show_activity=False).values('user_id');outgoing=Block.objects.filter(user=user).values('target_id');incoming=Block.objects.filter(target=user).values('user_id')
    query=Diary.objects.filter(user_id__in=ids,is_public=True).exclude(user_id__in=hidden).exclude(user_id__in=outgoing).exclude(user_id__in=incoming).select_related('user').order_by('-id')
    rows,total,_=paginated(query,request)
    return Response({'total_pages':total,'results':[{key:getattr(e,key) for key in ('id','movie','rating','review','spoilers','created_at')}|{'username':e.user.username,'display_name':e.user.display_name} for e in rows]})

@endpoint('GET','PATCH')
def preferences(request):
    user=required(request)
    if request.method=='PATCH':user.hide_spoilers=parse(schemas.Preferences,request.data).hide_spoilers;user.save(update_fields=['hide_spoilers'])
    return Response({'hide_spoilers':user.hide_spoilers})

@endpoint('GET')
def stats(request):
    rows=list(Diary.objects.filter(user=required(request)).values('movie_id','rating','watched_on'));rated=[r['rating'] for r in rows if r['rating'] is not None]
    return Response({'viewings':len(rows),'unique_films':len({r['movie_id'] for r in rows}),'rewatches':len(rows)-len({r['movie_id'] for r in rows}),'average_rating':sum(rated)/len(rated) if rated else None,'months':dict(sorted(Counter(r['watched_on'].strftime('%Y-%m') for r in rows).items())),'ratings':dict(sorted(Counter(str(r['rating']) for r in rows if r['rating'] is not None).items(),key=lambda item:float(item[0])))})

@endpoint('POST','DELETE')
def block(request,username):
    user=required(request);target=member(username)
    if user.id==target.id:raise Problem(422,'You cannot block yourself.')
    if request.method=='DELETE':Block.objects.filter(user=user,target=target).delete()
    else:
        with transaction.atomic():Block.objects.get_or_create(user=user,target=target);Follow.objects.filter(Q(follower=user,followee=target)|Q(follower=target,followee=user)).delete()
    return Response(status=204)

@endpoint('POST')
def report(request,username):
    user=required(request);target=member(username);data=parse(schemas.Report,request.data)
    if user.id==target.id:raise Problem(422,'You cannot report yourself.')
    if len(data.reason.strip())<10:raise Problem(422,'Describe the problem in at least 10 characters.')
    Report.objects.create(user=user,target=target,reason=data.reason.strip());return Response({'message':'Report saved for the site administrator.'},status=201)

@endpoint('GET')
def people(request,username):
    target=member(username);kind=request.query_params.get('kind','followers')
    if kind not in ('followers','following'):raise Problem(422,'Invalid member list.')
    from .common import page
    number=page(request);query=User.objects.filter(following__followee=target) if kind=='followers' else User.objects.filter(followers__follower=target)
    rows=list(query.order_by('username').values('username','display_name')[(number-1)*20:number*20+1]);return Response({'results':rows[:20],'has_more':len(rows)>20})

@endpoint('GET')
def compare(request,username):
    user=required(request);target=member(username)
    def ratings(u):return {r['movie_id']:r['rating'] for r in Diary.objects.filter(user=u,is_public=True,rating__isnull=False).order_by('id').values('movie_id','rating')}
    a,b=ratings(user),ratings(target);shared=a.keys()&b.keys();mine={m['id'] for m in Favorite.objects.filter(user=user).values_list('movie',flat=True)}
    details=ProfileDetails.objects.filter(user=target).first();theirs=list(Favorite.objects.filter(user=target).order_by('position').values_list('movie',flat=True)) if not details or details.show_favorites else []
    return Response({'shared_rated_films':len(shared),'average_rating_difference':sum(abs(a[id]-b[id]) for id in shared)/len(shared) if shared else None,'shared_favorites':[m for m in theirs if m['id'] in mine]})
