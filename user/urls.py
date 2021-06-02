from django.urls import path
from . import views

urlpatterns = [
    path('', views.user_profile),
    path('register/', views.user_register),
    path('login/', views.user_login),
    path('logout/', views.user_logout),
    path('refresh-token/', views.refresh_token_view),
    path('delete_account/', views.user_delete),
]
