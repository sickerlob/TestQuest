
from django.contrib import admin
from django.urls import path
from Forum import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.forum_home_view, name='forum_home'),
    path('new-post/', views.create_post_view, name='create_post'),
    path('profile/', views.profile_view, name='profile'),
    path('guest-login/', views.guest_login_view, name='guest_login'),
    path('post/<int:post_id>/', views.post_detail_view, name='post_detail'),
]