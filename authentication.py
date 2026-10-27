import hashlib,hmac,time
from django.contrib.auth.hashers import BasePasswordHasher,mask_hash
from rest_framework.authentication import BaseAuthentication
from .models import ApiSession

class LegacyScryptHasher(BasePasswordHasher):
    algorithm='frame_scrypt'
    def encode(self,password,salt):return f'{self.algorithm}${salt}${hashlib.scrypt(password.encode(),salt=bytes.fromhex(salt),n=16384,r=8,p=1).hex()}'
    def verify(self,password,encoded):
        try:_,salt,_=encoded.split('$');return hmac.compare_digest(encoded,self.encode(password,salt))
        except (ValueError,TypeError):return False
    def safe_summary(self,encoded):
        _,salt,value=encoded.split('$');return {'algorithm':self.algorithm,'salt':mask_hash(salt),'hash':mask_hash(value)}
    def must_update(self,encoded):return False

class FrameCookieAuthentication(BaseAuthentication):
    def authenticate(self,request):
        token=request.COOKIES.get('frame_session','')
        if not token:return None
        session=ApiSession.objects.select_related('user').filter(token_hash=hashlib.sha256(token.encode()).hexdigest(),expires__gt=int(time.time()),user__is_active=True).first()
        if not session:return None
        return session.user,session
    def authenticate_header(self,request):return 'Session'
