from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm,UserChangeForm
from .models import User,Watchlist,Diary,FilmList,ListItem,ReviewLike,ReviewComment,Follow,Block,Report,ProfileDetails,Favorite,ProfileImage

@admin.register(User)
class FrameUserAdmin(UserAdmin):
    fieldsets=UserAdmin.fieldsets+(('FRAME profile',{'fields':('display_name','bio','country','birth_date','recovery_email','verified_recovery_email','hide_spoilers')}),)
    list_display=('username','display_name','email','is_staff','is_active')
    search_fields=('username','display_name','email')

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display=('id','user','target','created_at')
    search_fields=('reason','user__username','target__username')
    readonly_fields=('created_at',)

@admin.register(Diary)
class DiaryAdmin(admin.ModelAdmin):
    list_display=('id','user','movie_id','rating','is_public','watched_on')
    list_filter=('is_public','spoilers')
    search_fields=('review','user__username')

for model in (Watchlist,FilmList,ListItem,ReviewLike,ReviewComment,Follow,Block,ProfileDetails,Favorite):admin.site.register(model)

@admin.register(ProfileImage)
class ImageAdmin(admin.ModelAdmin):
    list_display=('user','kind','updated_at')
    exclude=('data',)
