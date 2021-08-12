from django.urls import path
from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^get-hospitals/$', views.get_hospitals_for_patients, name='get_hospitals'),
    url(r'^get-hospital/$', views.get_hospital_info, name='get_hospital_info'),
    url(r'^get-ven-providers/$', views.get_ven_providers, name='get_venProviders'),
    url(r'^get-coworkers/$', views.get_co_workers, name='get_coWorkers'),
    url(r'^hospital/get-patients/$', views.get_patients, name='get_patients_for_hospitals'),
    url(r'^hospital/get-admitted-patients/$', views.get_admitted_patients, name='get_admited_patients_for_hospitals'),
    url(r'^patient/submit-request/$', views.submit_request, name='submit_request'),
    url(r'^patient/cancel-request/$', views.cancel_admit_request, name='cancel_request'),
    url(r'^patient/answer-request/$', views.respond_patient_request, name='answer_request'),
    url(r'^patient/discharge/$', views.discharge_patient, name='discharge_patient'),
    url(r'^coworker/submit-request/$', views.coworker_submit_request, name='coworker_submit_request'),
    url(r'^coworker/cancel-request/$', views.coworker_cancel_request, name='coworker_cancel_request'),
    url(r'^coworker/answer-request/$', views.response_coworker_request, name='answer_work_request'),
    url(r'^coworker/remove-worker/$', views.remove_worker, name='remove coworker'),
]
