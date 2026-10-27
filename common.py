import hashlib,secrets,time
from functools import wraps
from django.conf import settings
from django.middleware.csrf import CsrfViewMiddleware
from django.http import HttpResponse
from rest_framework.decorators import api_view
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.response import Response
from rest_framework.exceptions import APIException,NotAuthenticated,NotFound
from rest_framework.views import exception_handler as drf_exception_handler
from pydantic import ValidationError
from .models import ApiSession,User

class Problem(APIException):
    def __init__(self,status,detail):self.status_code=status;super().__init__(detail)

def exception_handler(exc,context):
    response=drf_exception_handler(exc,context)
    if response is not None and 'detail' not in response.data:response.data={'detail':response.data}
    return response

def endpoint(*methods):
    def decorate(function):
        @wraps(function)
        def checked(request,*args,**kwargs):
            if request.method not in ('GET','HEAD','OPTIONS'):
                failure=CsrfViewMiddleware(lambda r:HttpResponse()).process_view(request._request,lambda r:HttpResponse(),(),{})
                if failure:return Response({'detail':'Security token expired. Refresh and try again.','code':'CSRF_FAILED'},status=403)
            return function(request,*args,**kwargs)
        view=api_view(list(methods))(checked)
        if function.__name__ in ('signup','login','request_reset','verify_email','confirm_reset','resend'):
            view.cls.throttle_classes=[ScopedRateThrottle]
            view.cls.throttle_scope='account'
        return view
    return decorate

def parse(model,data):
    try:return model.model_validate(data)
    except ValidationError as e:raise Problem(422,' '.join(error['msg'] for error in e.errors(include_input=False)))

def required(request):
    if not request.user.is_authenticated:raise NotAuthenticated('Please sign in to continue.')
    return request.user

def member(username):
    user=User.objects.filter(username=username.lower(),is_active=True).first()
    if not user:raise NotFound('Member not found.')
    return user

def public(user):return {k:getattr(user,k) for k in ('id','username','display_name','bio','country')}

def new_session(response,user):
    token=secrets.token_urlsafe(32);ApiSession.objects.filter(expires__lte=int(time.time())).delete()
    ApiSession.objects.create(token_hash=hashlib.sha256(token.encode()).hexdigest(),user=user,expires=int(time.time())+604800)
    response.set_cookie('frame_session',token,max_age=604800,httponly=True,secure=settings.CSRF_COOKIE_SECURE,samesite='Lax',path='/api')
    return response

def page(request,max_value=10000):
    try:value=int(request.query_params.get('page','1'))
    except ValueError:raise Problem(422,'Invalid page.')
    if not 1<=value<=max_value:raise Problem(422,'Invalid page.')
    return value

def paginated(query,request):
    number=page(request);count=query.count()
    return query[(number-1)*20:number*20],max(1,(count+19)//20),number

def serialize_entry(entry,private=True):
    data={key:getattr(entry,key) for key in ('id','movie_id','user_id','movie','rating','review','spoilers','is_public','created_at','updated_at')}
    if private:data['watched_on']=entry.watched_on.isoformat()
    return data
