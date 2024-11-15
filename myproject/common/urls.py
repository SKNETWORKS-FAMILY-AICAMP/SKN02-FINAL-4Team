from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'common'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('signup/', views.signup, name='signup'),
    path('profile/', views.profile, name='profile'),
    path("update-profile-image/", views.update_profile_image, name="update_profile_image"),
    path('delete-account/', views.delete_account, name='delete_account'),
]