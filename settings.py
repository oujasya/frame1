import os
from pathlib import Path
from django.core.exceptions import ImproperlyConfigured
from django.core.management.utils import get_random_secret_key
from dotenv import load_dotenv
import dj_database_url
BASE_DIR=Path(__file__).resolve().parent.parent
# Deployment environment wins; Neon root env files precede backend-local defaults.
_explicit_database=os.getenv('DJANGO_DATABASE_URL') or os.getenv('DATABASE_URL')
load_dotenv(BASE_DIR.parent/'.env.local')
load_dotenv(BASE_DIR.parent/'.env')
load_dotenv(BASE_DIR/'.env')
DEBUG=os.getenv('DJANGO_DEBUG','true').lower()=='true'
SECRET_KEY=os.getenv('DJANGO_SECRET_KEY','')
if not SECRET_KEY:
    if not DEBUG:raise ImproperlyConfigured('Set DJANGO_SECRET_KEY for production.')
    keyfile=BASE_DIR/'data/django-secret.key';keyfile.parent.mkdir(parents=True,exist_ok=True)
    if not keyfile.exists():keyfile.write_text(get_random_secret_key(),encoding='utf-8')
    SECRET_KEY=keyfile.read_text(encoding='utf-8')
ALLOWED_HOSTS=[v.strip() for v in os.getenv('DJANGO_ALLOWED_HOSTS','localhost,127.0.0.1,testserver').split(',')]
render_hostname=os.getenv('RENDER_EXTERNAL_HOSTNAME','').strip()
if render_hostname:
    if render_hostname not in ALLOWED_HOSTS:ALLOWED_HOSTS.append(render_hostname)
    os.environ.setdefault('APP_PUBLIC_URL','https://'+render_hostname)
INSTALLED_APPS=['django.contrib.admin','django.contrib.auth','django.contrib.contenttypes','django.contrib.sessions','django.contrib.messages','django.contrib.staticfiles','corsheaders','rest_framework','core']
MIDDLEWARE=['django.middleware.security.SecurityMiddleware','whitenoise.middleware.WhiteNoiseMiddleware','corsheaders.middleware.CorsMiddleware','django.contrib.sessions.middleware.SessionMiddleware','django.middleware.common.CommonMiddleware','django.middleware.csrf.CsrfViewMiddleware','django.contrib.auth.middleware.AuthenticationMiddleware','django.contrib.messages.middleware.MessageMiddleware','django.middleware.clickjacking.XFrameOptionsMiddleware']
ROOT_URLCONF='config.urls'
TEMPLATES=[{'BACKEND':'django.template.backends.django.DjangoTemplates','DIRS':[],'APP_DIRS':True,'OPTIONS':{'context_processors':['django.template.context_processors.request','django.contrib.auth.context_processors.auth','django.contrib.messages.context_processors.messages']}}]
WSGI_APPLICATION='config.wsgi.application'
ASGI_APPLICATION='config.asgi.application'
AUTH_USER_MODEL='core.User'
PASSWORD_HASHERS=['django.contrib.auth.hashers.PBKDF2PasswordHasher','core.authentication.LegacyScryptHasher']
database=_explicit_database or os.getenv('DATABASE_URL') or os.getenv('DJANGO_DATABASE_URL','')
if os.getenv('FRAME_DATABASE_DIRECT')=='1':
    database=os.getenv('DATABASE_URL_UNPOOLED') or database
DATABASES={'default':dj_database_url.parse(database,conn_max_age=60,conn_health_checks=True) if database else {'ENGINE':'django.db.backends.sqlite3','NAME':os.getenv('DJANGO_SQLITE_PATH',str(BASE_DIR/'data/frame-django.sqlite3')),'OPTIONS':{'timeout':20}}}
if DATABASES['default']['ENGINE']=='django.db.backends.postgresql':
    # Transaction pooling cannot retain session-level cursors or prepared statements.
    DATABASES['default']['DISABLE_SERVER_SIDE_CURSORS']=True
    DATABASES['default'].setdefault('OPTIONS',{}).update(connect_timeout=20,prepare_threshold=None)
    if os.getenv('FRAME_TEST_DATABASE_NAME'):
        DATABASES['default']['TEST']={'NAME':os.environ['FRAME_TEST_DATABASE_NAME']}
DEFAULT_AUTO_FIELD='django.db.models.BigAutoField'
USE_TZ=True
TIME_ZONE='Asia/Kolkata'
LANGUAGE_CODE='en-us'
STATIC_URL='/static/'
STATIC_ROOT=BASE_DIR/'staticfiles'
FRONTEND_DIST=Path(os.getenv('FRAME_FRONTEND_DIST',str(BASE_DIR.parent/'frontend/dist')))
WHITENOISE_ROOT=str(FRONTEND_DIST)
STORAGES={'default':{'BACKEND':'django.core.files.storage.FileSystemStorage'},'staticfiles':{'BACKEND':'whitenoise.storage.CompressedManifestStaticFilesStorage'}}
CORS_ALLOWED_ORIGINS=[v.strip() for v in os.getenv('CORS_ORIGINS','http://localhost:5173,http://127.0.0.1:5173').split(',')]
CORS_ALLOW_CREDENTIALS=True
if render_hostname and not os.getenv('CORS_ORIGINS'):CORS_ALLOWED_ORIGINS=['https://'+render_hostname]
CSRF_TRUSTED_ORIGINS=list(CORS_ALLOWED_ORIGINS)
if render_hostname and 'https://'+render_hostname not in CSRF_TRUSTED_ORIGINS:CSRF_TRUSTED_ORIGINS.append('https://'+render_hostname)
CSRF_COOKIE_HTTPONLY=True
CSRF_COOKIE_SECURE=os.getenv('COOKIE_SECURE','false').lower()=='true'
SESSION_COOKIE_SECURE=CSRF_COOKIE_SECURE
SESSION_COOKIE_NAME='django_admin_session'
APPEND_SLASH=False
REST_FRAMEWORK={'DEFAULT_AUTHENTICATION_CLASSES':['core.authentication.FrameCookieAuthentication'],'DEFAULT_PERMISSION_CLASSES':['rest_framework.permissions.AllowAny'],'DEFAULT_RENDERER_CLASSES':['rest_framework.renderers.JSONRenderer'],'EXCEPTION_HANDLER':'core.common.exception_handler','DEFAULT_THROTTLE_CLASSES':['rest_framework.throttling.AnonRateThrottle','rest_framework.throttling.UserRateThrottle'],'DEFAULT_THROTTLE_RATES':{'anon':'600/min','user':'1200/min','account':'20/min'}}
EMAIL_BACKEND='django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST=os.getenv('SMTP_HOST','')
EMAIL_PORT=int(os.getenv('SMTP_PORT','587'))
EMAIL_HOST_USER=os.getenv('SMTP_USERNAME','')
EMAIL_HOST_PASSWORD=os.getenv('SMTP_PASSWORD','')
EMAIL_USE_SSL=EMAIL_PORT==465
EMAIL_USE_TLS=not EMAIL_USE_SSL
EMAIL_TIMEOUT=10
DEFAULT_FROM_EMAIL=os.getenv('SMTP_FROM','')
DATA_UPLOAD_MAX_MEMORY_SIZE=3_000_000
SECURE_CONTENT_TYPE_NOSNIFF=True
X_FRAME_OPTIONS='DENY'
SECURE_SSL_REDIRECT=os.getenv('DJANGO_SECURE_SSL_REDIRECT','false').lower()=='true'
SECURE_HSTS_SECONDS=int(os.getenv('DJANGO_HSTS_SECONDS','0'))

# Render terminates TLS at its trusted reverse proxy.
if os.getenv('DJANGO_TRUST_PROXY','false').lower()=='true':
    SECURE_PROXY_SSL_HEADER=('HTTP_X_FORWARDED_PROTO','https')
