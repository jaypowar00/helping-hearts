from django.urls import path
from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^get-hospitals/$', views.get_hospitals_for_patients, name='get_hospitals_for_patients'),
    url(r'^get-hospital/$', views.get_hospital_info, name='get_hospital_info'),
    url(r'^get-ven-providers/$', views.get_ven_providers, name='get_venProviders'),
    url(r'^get-coworkers/$', views.get_co_workers, name='get_coWorkers')

]
