from django.urls import path
from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^patients/get-hospitals/$', views.get_hospitals_for_patients, name='get_hospitals_for_patients'),
    url(r'^patients/get-hospital-info/$', views.get_hospital_info, name='get_hospital_info'),
    url(r'^patients/get-ventilator-provider-info/$', views.get_venProviders, name='get_venProviders'),

]
