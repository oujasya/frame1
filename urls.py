from django.contrib import admin
from django.urls import path
from core.frontend import homepage
from core import accounts_views as a,movies as m,journal_views as j,lists_views as l,social_views as s,profiles_views as p
urlpatterns=[
 path('',homepage),
 path('admin/',admin.site.urls),
 path('api/csrf',a.csrf),path('api/health',m.health),
 path('api/auth/signup',a.signup),path('api/auth/login',a.login),path('api/auth/logout',a.logout),path('api/auth/me',a.me),
 path('api/account',a.account),path('api/account/password',a.change_password),path('api/account/recovery-email',a.recovery_email),path('api/account/verification/send',a.resend),path('api/auth/email/verify',a.verify_email),path('api/auth/password-reset/request',a.request_reset),path('api/auth/password-reset/confirm',a.confirm_reset),
 path('api/profiles/me',a.edit_profile),
 path('api/movies/trending',m.collection,{'kind':'trending'}),path('api/movies/popular',m.collection,{'kind':'popular'}),path('api/movies/top-rated',m.collection,{'kind':'top-rated'}),path('api/movies/country',m.collection,{'kind':'country'}),path('api/movies/search',m.search),path('api/movies/<int:movie_id>',m.detail),path('api/movies/<int:movie_id>/watch-providers',m.providers),path('api/movies/<int:movie_id>/reviews',j.reviews),path('api/artwork/tmdb/<str:size>/<str:filename>',m.artwork),
 path('api/watchlist',j.watchlist),path('api/watchlist/<int:movie_id>',j.remove_watchlist),path('api/diary',j.diary),path('api/diary/<int:entry_id>',j.diary_entry),
 path('api/lists',l.lists),path('api/lists/<int:list_id>',l.detail),path('api/lists/<int:list_id>/movies',l.add_movie),path('api/lists/<int:list_id>/movies/<int:movie_id>',l.list_movie),
 path('api/reviews/<int:review_id>/reactions',s.reactions),path('api/reviews/<int:review_id>/like',s.like),path('api/reviews/<int:review_id>/comments',s.comments),path('api/reviews/<int:review_id>/comments/<int:comment_id>',s.delete_comment),
 path('api/members',s.members),path('api/feed',s.feed),path('api/preferences',s.preferences),path('api/stats',s.stats),
 path('api/profiles/<str:username>',p.profile),path('api/profiles/<str:username>/activity',p.activity),path('api/profiles/<str:username>/lists',p.public_lists),path('api/profiles/<str:username>/details',p.details),path('api/profiles/<str:username>/images/<str:kind>',p.image),path('api/profiles/<str:username>/people',s.people),path('api/profiles/<str:username>/compare',s.compare),path('api/profiles/<str:username>/connections',s.connections),path('api/profiles/<str:username>/follow',s.follow),path('api/profiles/<str:username>/block',s.block),path('api/profiles/<str:username>/report',s.report),
 path('api/profile/details',p.update_details),path('api/profile/favorites',p.favorites),path('api/profile/images/<str:kind>',p.upload_image),
]
admin.site.site_header='FRAME administration'
admin.site.site_title='FRAME admin'
admin.site.index_title='Accounts, films and community moderation'
