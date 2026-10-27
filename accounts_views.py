import hashlib,time
from django.db import transaction,IntegrityError
from django.contrib.auth import authenticate
from django.middleware.csrf import get_token
from django.contrib.auth.hashers import make_password
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from . import schemas
from .models import User,ApiSession,PasswordReset,EmailVerification
from .common import endpoint,parse,required,public,new_session,Problem
from . import mail

@endpoint('GET')
def csrf(request):return Response({'csrf_token':get_token(request._request)})

@endpoint('POST')
def signup(request):
    data=parse(schemas.Signup,request.data)
    import re
    username=data.username.strip().lower()
    if not re.fullmatch('[a-z0-9_]{3,24}',username):raise Problem(422,'Use 3–24 letters, numbers or underscores for your username.')
    try:
        with transaction.atomic():user=User.objects.create_user(username=username,password=data.password,display_name=username,country=data.country,email=data.email,birth_date=data.birth_date,recovery_email=data.email)
    except IntegrityError:raise Problem(409,'That username or Gmail address is already in use.')
    sent=False
    try:mail.issue_verification(user);sent=True
    except Problem:pass
    return new_session(Response({**public(user),'email_verification_sent':sent},status=201),user)

@endpoint('POST')
def login(request):
    data=parse(schemas.Credentials,request.data)
    user=authenticate(request._request,username=data.username.strip().lower(),password=data.password)
    if not user:raise Problem(401,'Username or password is incorrect.')
    return new_session(Response(public(user)),user)

@endpoint('POST')
def logout(request):
    token=request.COOKIES.get('frame_session','');ApiSession.objects.filter(token_hash=hashlib.sha256(token.encode()).hexdigest()).delete()
    response=Response(status=204);response.delete_cookie('frame_session',path='/api',samesite='Lax');return response

@endpoint('GET')
def me(request):return Response(public(required(request)))

@endpoint('PATCH')
def edit_profile(request):
    user=required(request);data=parse(schemas.Profile,request.data)
    if not data.display_name.strip():raise Problem(422,'Display name is required.')
    user.display_name=data.display_name.strip();user.bio=data.bio.strip()
    if 'country' in data.model_fields_set:user.country=data.country
    user.save();return Response(public(user))

def account_data(user):
    verified=bool(user.recovery_email and user.verified_recovery_email==user.recovery_email)
    return {'recovery_email':user.recovery_email or '','email_verified':verified,'mail_delivery_configured':mail.configured(),'password_recovery_available':bool(verified and mail.configured())}

@endpoint('GET','DELETE')
def account(request):
    user=required(request)
    if request.method=='GET':return Response(account_data(user))
    data=parse(schemas.DeleteAccount,request.data)
    if data.confirmation!=user.username:raise Problem(422,'Type your username exactly to confirm deletion.')
    if not user.check_password(data.current_password):raise Problem(403,'Current password is incorrect.')
    user.delete();response=Response(status=204);response.delete_cookie('frame_session',path='/api',samesite='Lax');return response

@endpoint('POST')
def change_password(request):
    user=required(request);data=parse(schemas.PasswordChange,request.data)
    if not user.check_password(data.current_password):raise Problem(403,'Current password is incorrect.')
    with transaction.atomic():
        user.set_password(data.new_password);user.save(update_fields=['password']);ApiSession.objects.filter(user=user).delete();PasswordReset.objects.filter(user=user).delete()
    return new_session(Response({'message':'Password changed. Other sessions have been signed out.'}),user)

@endpoint('PATCH')
def recovery_email(request):
    user=required(request);data=parse(schemas.RecoveryEmail,request.data)
    if not user.check_password(data.current_password):raise Problem(403,'Current password is incorrect.')
    try:
        with transaction.atomic():
            if data.email!=user.recovery_email:user.verified_recovery_email=None
            user.recovery_email=data.email;user.save(update_fields=['recovery_email','verified_recovery_email']);EmailVerification.objects.filter(user=user).delete();PasswordReset.objects.filter(user=user).delete()
    except IntegrityError:raise Problem(409,'That recovery address cannot be used.')
    message='Recovery email saved.'
    if user.verified_recovery_email!=user.recovery_email:
        try:mail.issue_verification(user);message+=' Verification email sent. Check your inbox.'
        except Problem as error:message+=' '+str(error.detail)
    return Response({**account_data(user),'message':message})

@endpoint('POST')
def resend(request):
    user=required(request)
    if not user.recovery_email:raise Problem(422,'Add a recovery email in Settings first.')
    if user.verified_recovery_email==user.recovery_email:return Response({'message':'Your recovery email is already verified.'})
    mail.issue_verification(user);return Response({'message':'Verification email sent. Check your inbox and spam folder.'})

@endpoint('POST')
def verify_email(request):
    data=parse(schemas.Verify,request.data)
    with transaction.atomic():
        row=EmailVerification.objects.select_for_update().select_related('user').filter(token_hash=hashlib.sha256(data.token.encode()).hexdigest(),expires__gt=int(time.time())).first()
        if not row or row.email!=row.user.recovery_email:raise Problem(400,'Verification link is invalid or expired. Request a new one from Settings.')
        row.user.verified_recovery_email=row.email;row.user.save(update_fields=['verified_recovery_email']);EmailVerification.objects.filter(user=row.user).delete()
    return Response({'message':'Your email is verified. You can now use it to recover your account.'})

@endpoint('POST')
def request_reset(request):
    data=parse(schemas.ResetRequest,request.data);mail.request_reset(data.email.strip().lower())
    return Response({'message':'If this address is registered and verified for recovery, a reset link will be emailed.'})

@endpoint('POST')
def confirm_reset(request):
    data=parse(schemas.ResetPassword,request.data)
    with transaction.atomic():
        row=PasswordReset.objects.select_for_update().select_related('user').filter(token_hash=hashlib.sha256(data.token.encode()).hexdigest(),expires__gt=int(time.time())).first()
        if not row or not row.user.recovery_email or row.user.recovery_email!=row.user.verified_recovery_email:raise Problem(400,'Reset link is invalid or expired. Request a new one.')
        user=row.user;user.set_password(data.new_password);user.save(update_fields=['password']);PasswordReset.objects.filter(user=user).delete();ApiSession.objects.filter(user=user).delete()
    return Response({'message':'Password reset. Please log in with your new password.'})
