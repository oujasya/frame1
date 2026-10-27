import hashlib,secrets,time,os,smtplib
from django.conf import settings
from django.core.mail import EmailMessage
from django.db import transaction
from .models import User,EmailSendLimit,ResetSendLimit,EmailVerification,PasswordReset
from .common import Problem

def configured():return bool(settings.EMAIL_HOST and settings.DEFAULT_FROM_EMAIL and os.getenv('APP_PUBLIC_URL','').strip())
def deliver(email,token,kind):
    verification=kind=='verify';path='verify-email' if verification else 'reset-password'
    url=os.environ['APP_PUBLIC_URL'].rstrip('/')+'/#/'+path+'?token='+token
    subject='Verify your FRAME email' if verification else 'Reset your FRAME password'
    body=('Confirm this email belongs to you. This link expires after 24 hours.' if verification else 'Choose your new FRAME password. This link expires after 30 minutes.')+'\n\n'+url+'\n\nIf you did not request this, ignore this email.'
    EmailMessage(subject,body,settings.DEFAULT_FROM_EMAIL,[email]).send(fail_silently=False)

def issue_verification(user):
    if not configured():raise Problem(503,'Email delivery is not configured yet. Your address is saved; verification can be sent after setup.')
    token=secrets.token_urlsafe(32);digest=hashlib.sha256(token.encode()).hexdigest();now=int(time.time())
    with transaction.atomic():
        User.objects.select_for_update().get(pk=user.pk)
        limit=EmailSendLimit.objects.filter(user=user).first()
        if limit and now-limit.last_sent<60:raise Problem(429,'Please wait a minute before requesting another verification email.')
        EmailVerification.objects.filter(user=user).delete();EmailVerification.objects.filter(expires__lte=now).delete();EmailVerification.objects.create(token_hash=digest,user=user,email=user.recovery_email,expires=now+86400);EmailSendLimit.objects.update_or_create(user=user,defaults={'last_sent':now})
    try:deliver(user.recovery_email,token,'verify')
    except (OSError,smtplib.SMTPException,ValueError):
        EmailVerification.objects.filter(pk=digest).delete();raise Problem(503,'Verification email could not be delivered. Please try again shortly.')

def request_reset(email):
    if not configured():raise Problem(503,'Password recovery email is not configured. Contact the site administrator.')
    now=int(time.time());key=hashlib.sha256(email.encode()).hexdigest()
    with transaction.atomic():
        row,_=ResetSendLimit.objects.select_for_update().get_or_create(address_hash=key,defaults={'last_sent':0})
        if now-row.last_sent<60:raise Problem(429,'Please wait a minute before requesting another reset.')
        row.last_sent=now;row.save()
    user=User.objects.filter(recovery_email=email,verified_recovery_email=email,is_active=True).first()
    if user:
        token=secrets.token_urlsafe(32);digest=hashlib.sha256(token.encode()).hexdigest()
        with transaction.atomic():PasswordReset.objects.filter(user=user).delete();PasswordReset.objects.create(token_hash=digest,user=user,expires=now+1800)
        try:deliver(email,token,'reset')
        except (OSError,smtplib.SMTPException,ValueError):
            PasswordReset.objects.filter(pk=digest).delete();raise Problem(503,'Recovery email is temporarily unavailable. Please try again later.')
