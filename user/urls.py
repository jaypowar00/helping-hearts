from django.urls import path
from . import views

urlpatterns = [
    path('user/', views.user_profile),
    path('user/register', views.user_register),
    path('user/login', views.user_login),
    path('user/logout', views.user_logout),
    path('user/refresh-token', views.refresh_token_view),
    path('user/delete_account', views.user_delete),
]
