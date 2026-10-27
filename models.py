from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

class User(AbstractUser):
    password=models.CharField(max_length=255)
    email=models.EmailField(null=True,blank=True,unique=True)
    display_name=models.CharField(max_length=60)
    bio=models.CharField(max_length=280,blank=True,default='')
    country=models.CharField(max_length=2,null=True,blank=True)
    birth_date=models.DateField(null=True,blank=True)
    recovery_email=models.EmailField(null=True,blank=True,unique=True)
    verified_recovery_email=models.EmailField(null=True,blank=True)
    hide_spoilers=models.BooleanField(default=True)
    def __str__(self):return self.username

class ApiSession(models.Model):
    token_hash=models.CharField(max_length=64,primary_key=True)
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    expires=models.BigIntegerField(db_index=True)

class Watchlist(models.Model):
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    movie_id=models.PositiveBigIntegerField()
    movie=models.JSONField()
    class Meta:constraints=[models.UniqueConstraint(fields=['user','movie_id'],name='unique_watchlist_film')]

class Diary(models.Model):
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    movie_id=models.PositiveBigIntegerField(db_index=True)
    movie=models.JSONField()
    rating=models.FloatField(null=True,blank=True)
    review=models.TextField(blank=True,default='')
    watched_on=models.DateField(db_index=True)
    spoilers=models.BooleanField(default=False)
    is_public=models.BooleanField(default=True,db_index=True)
    created_at=models.DateTimeField(default=timezone.now)
    updated_at=models.DateTimeField(default=timezone.now)

class FilmList(models.Model):
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    name=models.CharField(max_length=100)
    description=models.TextField(blank=True,default='')
    is_public=models.BooleanField(default=False)
    created_at=models.DateTimeField(default=timezone.now)
    def __str__(self):return self.name

class ListItem(models.Model):
    film_list=models.ForeignKey(FilmList,on_delete=models.CASCADE,related_name='items')
    movie_id=models.PositiveBigIntegerField()
    movie=models.JSONField()
    position=models.IntegerField()
    class Meta:constraints=[models.UniqueConstraint(fields=['film_list','movie_id'],name='unique_list_film')]

class ReviewLike(models.Model):
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    review=models.ForeignKey(Diary,on_delete=models.CASCADE,related_name='likes')
    class Meta:constraints=[models.UniqueConstraint(fields=['user','review'],name='unique_review_like')]

class ReviewComment(models.Model):
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    review=models.ForeignKey(Diary,on_delete=models.CASCADE,related_name='comments')
    body=models.TextField()
    spoilers=models.BooleanField(default=False)
    created_at=models.DateTimeField(default=timezone.now)

class Follow(models.Model):
    follower=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='following')
    followee=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='followers')
    class Meta:constraints=[models.UniqueConstraint(fields=['follower','followee'],name='unique_follow')]

class Block(models.Model):
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='blocking')
    target=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='blocked_by')
    class Meta:constraints=[models.UniqueConstraint(fields=['user','target'],name='unique_block')]

class Report(models.Model):
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='reports_sent')
    target=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='reports_received')
    reason=models.TextField()
    created_at=models.DateTimeField(default=timezone.now)

class ProfileDetails(models.Model):
    user=models.OneToOneField(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,primary_key=True,related_name='profile_details')
    genres=models.CharField(max_length=200,blank=True,default='')
    show_favorites=models.BooleanField(default=True)
    show_stats=models.BooleanField(default=False)
    show_activity=models.BooleanField(default=True)
    pinned_review=models.ForeignKey(Diary,on_delete=models.SET_NULL,null=True,blank=True,related_name='+')
    pinned_list=models.ForeignKey(FilmList,on_delete=models.SET_NULL,null=True,blank=True,related_name='+')

class Favorite(models.Model):
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    position=models.PositiveSmallIntegerField()
    movie=models.JSONField()
    class Meta:constraints=[models.UniqueConstraint(fields=['user','position'],name='unique_favorite_slot'),models.CheckConstraint(condition=models.Q(position__lt=5),name='five_favorite_slots')]

class ProfileImage(models.Model):
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    kind=models.CharField(max_length=10)
    data=models.BinaryField()
    updated_at=models.DateTimeField(default=timezone.now)
    class Meta:constraints=[models.UniqueConstraint(fields=['user','kind'],name='unique_profile_image')]

class PasswordReset(models.Model):
    token_hash=models.CharField(max_length=64,primary_key=True)
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    expires=models.BigIntegerField()

class EmailVerification(models.Model):
    token_hash=models.CharField(max_length=64,primary_key=True)
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    email=models.EmailField()
    expires=models.BigIntegerField()

class EmailSendLimit(models.Model):
    user=models.OneToOneField(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,primary_key=True)
    last_sent=models.BigIntegerField()

class ResetSendLimit(models.Model):
    address_hash=models.CharField(max_length=64,primary_key=True)
    last_sent=models.BigIntegerField()

class LegacyImport(models.Model):
    source=models.CharField(max_length=1000,unique=True)
    imported_at=models.DateTimeField(default=timezone.now)
    counts=models.JSONField(default=dict)
