import jwt
import json
from django.conf import settings
from HelpingHearts.settings import blackListedTokens
from django.db.utils import IntegrityError
from django.middleware.csrf import get_token
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model
from user.serializers import UserSerializer, HospitalSerializer, VenProviderSerializer, PatientSerializer, \
    CoWorkerSerializer
from user.utils import generate_access_token, generate_refresh_token
from user.decorators import check_blacklisted_token
from user.models import User, Patient, VenProvider, CoWorker, Hospital
from django.core.paginator import *


@api_view(['GET'])
@check_blacklisted_token
def get_hospitals_for_patients(request):
    query_params = dict(request.query_params)
    print(query_params)
    UserModel = get_user_model()
    user = request.user
    if not user.is_authenticated:
        response = retrieve_hospitals_for_patients(query_params)
        return response
    user = UserModel.objects.filter(id=user.id).first()
    if user is None:
        return Response(
            {
                'status': False,
                'message': 'user associated with credentials does not exists anymore',
            }
        )
    if user.account_type == 1:
        return retrieve_hospitals_for_patients(query_params)
    else:
        return Response({'status': False, 'message': 'This feature is only for Guests and Patients!'})


def retrieve_hospitals_for_patients(query_params):
    hospitals = Hospital.objects.all()
    if ('cc_lt' in query_params and query_params['cc_lt'][0].isdigit) or\
            ('cc_gt' in query_params and query_params['cc_gt'][0].isdigit) or\
            ('beds_lt' in query_params and query_params['beds_lt'][0].isdigit) or\
            ('beds_gt' in query_params and query_params['beds_gt'][0].isdigit) or\
            ('ven_lt' in query_params and query_params['ven_lt'][0].isdigit) or\
            ('ven_gt' in query_params and query_params['ven_gt'][0].isdigit) or\
            ('ox_lt' in query_params and query_params['ox_lt'][0].isdigit) or\
            ('ox_gt' in query_params and query_params['ox_gt'][0].isdigit) or\
            ('order' in query_params and query_params['order'][0] in ['name_a', 'name_d', 'pin_a', 'pin_d', 'bed_a', 'bed_d', 'ven_a', 'ven_d', 'ox_a', 'ox_d']) or \
            ('s_name' in query_params and query_params['s_name'][0] != '') or\
            ('s_pin' in query_params and query_params['s_pin'][0].isdigit):
        if 's_name' in query_params and query_params['s_name'][0] != '':
            hospitals = (hospitals & Hospital.objects.filter(id__name__search=query_params['s_name'][0])) |\
                        (hospitals & Hospital.objects.filter(id__about__search=query_params['s_name'][0])) |\
                        (hospitals & Hospital.objects.filter(id__name__icontains=query_params['s_name'][0])) |\
                        (hospitals & Hospital.objects.filter(id__about__icontains=query_params['s_name'][0]))
        if 's_pin' in query_params and query_params['s_pin'][0].isdigit:
            hospitals = hospitals & Hospital.objects.filter(id__pincode__search=query_params['s_pin'][0])
        if 'cc_lt' in query_params and query_params['cc_lt'][0].isdigit:
            hospitals = hospitals & Hospital.objects.filter(corona_count__lte=query_params['cc_lt'][0])
        if 'cc_gt' in query_params and query_params['cc_gt'][0].isdigit:
            hospitals = hospitals & Hospital.objects.filter(corona_count__gte=query_params['cc_gt'][0])
        if 'beds_lt' in query_params and query_params['beds_lt'][0].isdigit:
            hospitals = hospitals & Hospital.objects.filter(beds__lte=query_params['beds_lt'][0])
        if 'beds_gt' in query_params and query_params['beds_gt'][0].isdigit:
            hospitals = hospitals & Hospital.objects.filter(beds__gte=query_params['beds_gt'][0])
        if 'ven_lt' in query_params and query_params['ven_lt'][0].isdigit:
            hospitals = hospitals & Hospital.objects.filter(ventilators__lte=query_params['ven_lt'][0])
        if 'ven_gt' in query_params and query_params['ven_gt'][0].isdigit:
            hospitals = hospitals & Hospital.objects.filter(ventilators__gte=query_params['ven_gt'][0])
        if 'ox_lt' in query_params and query_params['ox_lt'][0].isdigit:
            hospitals = hospitals & Hospital.objects.filter(oxygens__lte=query_params['ox_lt'][0])
        if 'ox_gt' in query_params and query_params['ox_gt'][0].isdigit:
            hospitals = hospitals & Hospital.objects.filter(oxygens__gte=query_params['ox_gt'][0])
        if 'order' in query_params and query_params['order'][0] in ['name_a', 'name_d', 'pin_a', 'pin_d', 'bed_a', 'bed_d', 'ven_a', 'ven_d', 'ox_a', 'ox_d']:
            order = '-' if query_params['order'][0].split('_')[1] == 'd' else ''
            orderby = query_params['order'][0].split('_')[0]
            if orderby == 'name':
                hospitals &= Hospital.objects.order_by(order+'id__name')
            elif orderby == 'pin':
                hospitals &= Hospital.objects.order_by(order+'id__pincode')
            elif orderby == 'bed':
                hospitals &= Hospital.objects.order_by(order+'beds')
            elif orderby == 'ven':
                hospitals &= Hospital.objects.order_by(order+'ventilators')
            elif orderby == 'ox':
                hospitals &= Hospital.objects.order_by(order+'oxygens')
    if len(hospitals) == 0:
        return Response(
            {
                'status': False,
                'message': 'there are no hospitals'
            }
        )
    serialized_hospitals = HospitalSerializer(hospitals, many=True).data
    paginator = Paginator(serialized_hospitals, 5)
    page_no = query_params['page'][0] if ('page' in query_params and query_params['page'][0].isdigit) else 1
    hosp_as_page = paginator.get_page(page_no)
    hospital_list = []
    for hospital in hosp_as_page:
        hospital.update(UserSerializer(User.objects.filter(id=hospital['id']).first()).data)
        del hospital['email']
        del hospital['about']
        del hospital['account_type']
        hospital_list.append(hospital)
    return Response(
        {
            'status': True,
            'next_page': hosp_as_page.next_page_number() if hosp_as_page.has_next() else None,
            'previous_page': hosp_as_page.previous_page_number() if hosp_as_page.has_previous() else None,
            'total_hospitals': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': hosp_as_page.number,
            'current_page_hospitals': len(hospital_list),
            'hospitals': hospital_list
        }
    )


@api_view(['GET'])
@check_blacklisted_token
def get_hospital_info(request):
    query_params = dict(request.query_params)
    print("Query params : ", query_params)
    if 'hid' not in query_params:
        return Response(
            {
                'status': False,
                'message': 'hospital id missing'
            })
    hid = query_params['hid'][0]
    if not hid.isdigit:
        return Response(
            {
                'status': False,
                'message': 'invalid hospital id'
            }
        )
    hospital = Hospital.objects.filter(id=hid).first()
    if not hospital:
        return Response(
            {
                'status': False,
                'message': 'Hospital does not exists!'
            }
        )
    serialized_hospital = HospitalSerializer(hospital).data
    user = User.objects.filter(id=hospital.id.id).first()
    serialized_user = UserSerializer(user).data
    serialized_hospital.update(serialized_user)
    return Response(
        {
            'status': True,
            'hospital': serialized_hospital
        }
    )


# Full List of ventilator providers
@api_view(['GET'])
def get_ven_providers(request):
    query_params = dict(request.query_params)
    UserModel = get_user_model()
    user = request.user
    if not user.is_authenticated:
        return Response(
            {
                'status': False,
                'message': 'user is not logged in',
            }
        )
    user = UserModel.objects.filter(id=user.id).first()
    if user is None:
        return Response(
            {
                'status': False,
                'message': 'user associated with credentials does not exists anymore',
            }
        )
    if user.account_type == 2:
        return retrieve_all_ventilator_providers(query_params)
    else:
        return Response(
            {
                'status': False,
                'message': 'Only accessible for the hospitals'
            }
        )


def retrieve_all_ventilator_providers(query_params):
    venProviders = VenProvider.objects.all()
    if ('ven_lt' in query_params and query_params['ven_lt'][0].isdigit) or\
            ('ven_gt' in query_params and query_params['ven_gt'][0].isdigit) or\
            ('p_name' in query_params and query_params['p_name'][0] != ''):
        if 'p_name' in query_params and query_params['p_name'][0] != '':
            venProviders = (venProviders & VenProvider.objects.filter(id__name__search=query_params['p_name'][0])) |\
                           (venProviders & VenProvider.objects.filter(id__about__search=query_params['p_name'][0])) | \
                           (venProviders & VenProvider.objects.filter(id__name__icontains=query_params['p_name'][0])) |\
                            (venProviders & VenProvider.objects.filter(id__about__icontains=query_params['p_name'][0]))

        if 'ven_lt' in query_params and query_params['ven_lt'][0].isdigit:
            venProviders = venProviders & VenProvider.objects.filter(total_ventilators__lte=query_params['ven_lt'][0])

        if 'ven_gt' in query_params and query_params['ven_gt'][0].isdigit:
            venProviders = venProviders & VenProvider.objects.filter(total_ventilators__gte=query_params['ven_gt'][0])

    if len(venProviders) == 0:
        return Response(
            {
                'status': False,
                'message': 'There are no Ventilator Providers'
            }
        )
    serialized_venProviders = VenProviderSerializer(venProviders, many=True).data
    paginator = Paginator(serialized_venProviders, 30)
    page_no = query_params['page'][0] if ('page' in query_params and query_params['page'][0].isdigit) else 1
    venpro_as_page = paginator.get_page(page_no)
    venProvider_list = []
    for venProvider in venpro_as_page:
        venProvider.update(UserSerializer(User.objects.filter(id=venProvider['id']).first()).data)
        del venProvider['account_type']
        venProvider_list.append(venProvider)

    return Response(
        {
            'status': True,
            'next_page': venpro_as_page.next_page_number() if venpro_as_page.has_next() else None,
            'privious_page': venpro_as_page.previous_page_number() if venpro_as_page.has_next() else None,
            'total_ventilator_providers': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page_ventilatos_providers': len(venProvider_list),
            'Ventilator_providers': venProvider_list
        }
    )



@api_view(['GET'])
def get_co_workers(request):
    query_params = dict(request.query_params)
    UserModel = get_user_model()
    user = request.user
    if not user.is_authenticated:
        return Response(
            {
                'status': False,
                'message': 'user is not logged in',
            }
        )
    user = UserModel.objects.filter(id=user.id).first()
    if user is None:
        return Response(
            {
                'status': False,
                'message': 'user associated with credentials does not exists anymore',
            }
        )

    if user.account_type == 2:
        return retrieve_co_workers(query_params)
    else:
        return Response(
            {
                'status': False,
                'message': 'Accessible for hospitals'
            }
        )


def retrieve_co_workers(query_params):
    coworkers = CoWorker.objects.all()
    if ('avail' in query_params and query_params['avail'][0] == ('T' or 'F')) or\
            ('c_name' in query_params and query_params['c_name'][0] != ''):
        if 'c_name' in query_params and query_params['c_name'][0] != '':
            coworkers = (coworkers & CoWorker.objects.filter(id__name__search=query_params['c_name'][0])) | \
                        (coworkers & CoWorker.objects.filter(id__about__search=query_params['c_name'][0])) | \
                        (coworkers & CoWorker.objects.filter(id__name__icontains=query_params['c_name'][0])) | \
                        (coworkers & CoWorker.objects.filter(id__about__icontains=query_params['c_name'][0]))

        if 'avail' in query_params and query_params['avail'][0] in ['T', 'F']:
            coworkers = coworkers & CoWorker.objects.filter(available=query_params['avail'][0] == 'T')

    if len(coworkers) == 0:
        return Response(
            {
                'status': False,
                'message': 'Co-Worker is not available'
            }
        )

    serialized_coworkers = CoWorkerSerializer(coworkers, many=True).data
    paginator = Paginator(serialized_coworkers, 30)
    page_no = query_params['page'][0] if ('page' in query_params and query_params['page'][0].isdigit) else 1
    cowork_as_page = paginator.get_page(page_no)
    coworker_list = []

    for coworker in cowork_as_page:
        coworker.update(UserSerializer(User.objects.filter(id=coworker['id']).first()).data)
        del coworker['account_type']
        coworker_list.append(coworker)

    return Response(
        {
            'status': True,
            'next_page': cowork_as_page.next_page_number() if cowork_as_page.has_next() else None,
            'privious_page': cowork_as_page.previous_page_number() if cowork_as_page.has_next() else None,
            'total_co_workers': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page_Coworker': len(coworker_list),
            'Cowrkers': coworker_list
        }
    )


@api_view(['GET'])
@check_blacklisted_token
def get_patients(request):
    user = request.user
    if not user.is_authenticated:
        return Response(
            {
                'status': False,
                'message': 'Not logged in'
            }
        )
    user = User.objects.filter(id=user.id).first()
    if user.account_type != 2:
        return Response(
            {
                'status': False,
                'message': 'This feature is only for hospitals'
            }
        )
    hospital = user.hospital
    requested_patients = hospital.patient_requested_hospital
    patients = []
    for patient in requested_patients.order_by('-ct_scan_score'):
        ser_patient = PatientSerializer(patient).data
        ser_patient.update(UserSerializer(User.objects.filter(id=ser_patient['id']).first()).data)
        patients.append(ser_patient)

    return Response(
        {
            'status': True,
            'patients': patients
        }
    )


@api_view(['GET'])
@check_blacklisted_token
def get_admitted_patients(request):
    user = request.user
    if not user.is_authenticated:
        return Response(
            {
                'status': False,
                'message': 'Not logged in'
            }
        )
    user = User.objects.filter(id=user.id).first()
    if user.account_type != 2:
        return Response(
            {
                'status': False,
                'message': 'This feature is only for hospitals'
            }
        )
    hospital = user.hospital
    requested_patients = hospital.patient_admitted_hospital
    patients = []
    for patient in requested_patients.all():
        ser_patient = PatientSerializer(patient).data
        ser_patient.update(UserSerializer(User.objects.filter(id=ser_patient['id']).first()).data)
        patients.append(ser_patient)

    return Response(
        {
            'status': True,
            'patients': patients
        }
    )


@api_view(['POST'])
@check_blacklisted_token
def respond_patient_request(request):
    user = request.user
    if not user.is_authenticated:
        return Response(
            {
                'status': False,
                'message': 'Not logged in'
            }
        )
    if user.account_type != 2:
        return Response(
            {
                'status': False,
                'message': 'This feature is only for hospitals'
            }
        )
    jsn = request.data
    if ('accept' not in jsn) or not ('pid' in jsn and type(jsn['pid']) == int):
        return Response(
            {
                'status': False,
                'message': 'Missing data in request'
            }
        )
    pid = jsn['pid']
    patient = Patient.objects.filter(id=pid).first()
    hospital = user.hospital
    if not patient:
        return Response(
            {
                'status': False,
                'message': 'Patient does not exists!'
            }
        )
    if jsn['accept']:
        patient.admitted_hospital = patient.requested_hospital
        patient.requested_hospital = None
        patient.admit_request = False
        patient.admitted = True
        patient.save()
        if patient.bed_type == 1:
            if hospital.beds > 0:
                hospital.beds -= 1
                hospital.corona_count += 1
                hospital.save()
            else:
                return Response(
                    {
                        'status': False,
                        'message': 'Not enough required beds remaining to admit the patient!'
                    }
                )
        elif patient.bed_type == 2:
            if hospital.beds > 0 and hospital.ventilators > 0:
                hospital.beds -= 1
                hospital.ventilators -= 1
                hospital.corona_count += 1
                hospital.save()
            else:
                return Response(
                    {
                        'status': False,
                        'message': 'Not enough required beds remaining to admit the patient!'
                    }
                )
        else:
            if hospital.beds > 0 and hospital.oxygens > 0:
                hospital.beds -= 1
                hospital.oxygens -= 1
                hospital.corona_count += 1
                hospital.save()
            else:
                return Response(
                    {
                        'status': False,
                        'message': 'Not enough required beds remaining to admit the patient!'
                    }
                )
        return Response(
            {
                'status': True,
                'message': 'Patient Successfully admitted!'
            }
        )
    else:
        patient.requested_hospital = None
        patient.admit_request = False
        patient.save()
        return Response(
            {
                'status': True,
                'message': 'Patients admit request declined!'
            }
        )


@api_view(['POST'])
@check_blacklisted_token
def submit_request(request):
    jsn = request.data
    user = request.user
    if not user.is_authenticated:
        return Response(
            {
                'status': False,
                'message': 'Not logged in'
            }
        )
    if user.account_type != 1:
        return Response(
            {
                'status': False,
                'message': 'This feature is only for Patients'
            }
        )
    user = User.objects.filter(id=user.id).first()
    if not user:
        return Response(
            {
                'status': False,
                'message': 'User not found!'
            }
        )
    patient = user.patient
    if not ('hid' in jsn and type(jsn['hid']) == int):
        return Response(
            {
                'status': False,
                'message': 'Missing data in request'
            }
        )
    hospital = Hospital.objects.filter(id=jsn['hid']).first()
    if not hospital:
        return Response(
            {
                'status': False,
                'message': 'requesting hospital does not exists!'
            }
        )
    if patient.admit_request:
        return Response(
            {
                'status': False,
                'message': 'Patient can not submit another request while previous one is pending'
            }
        )
    if patient.admitted:
        return Response(
            {
                'status': False,
                'message': 'Already Admitted Patients can not submit admit request'
            }
        )
    patient.requested_hospital = hospital
    patient.admit_request = True
    patient.save()
    return Response(
        {
            'status': True,
            'message': 'Admit request submitted!'
        }
    )


@api_view(['POST'])
@check_blacklisted_token
def discharge_patient(request):
    jsn = request.data
    user = request.user
    if not user.is_authenticated:
        return Response(
            {
                'status': False,
                'message': 'Not logged in'
            }
        )
    if user.account_type != 2:
        return Response(
            {
                'status': False,
                'message': 'This feature is only for hospitals'
            }
        )
    if 'pid' not in jsn:
        return Response(
            {
                'status': False,
                'message': 'Missing data in request'
            }
        )
    hospital = user.hospital
    patient = Patient.objects.filter(id=jsn['pid']).first()
    if not patient:
        return Response(
            {
                'status': False,
                'message': 'requested patient does not exists any more!'
            }
        )
    patient.admitted = False
    patient.admitted_hospital = None
    patient.save()
    if patient.bed_type == 1:
        hospital.beds += 1
        hospital.corona_count -= 1
        hospital.save()
    elif patient.bed_type == 2:
        hospital.beds += 1
        hospital.ventilators += 1
        hospital.corona_count -= 1
        hospital.save()
    else:
        hospital.beds += 1
        hospital.oxygens += 1
        hospital.corona_count -= 1
        hospital.save()
    return Response(
        {
            'status': True,
            'message': 'Patient discharged!'
        }
    )


@api_view(['POST'])
@check_blacklisted_token
def cancel_admit_request(request):
    user = request.user
    if not user.is_authenticated:
        return Response(
            {
                'status': False,
                'message': 'Not logged in!'
            }
        )
    patient = user.patient
    patient.admit_request = False
    patient.requested_hospital = None
    patient.save()
    return Response(
        {
            'status': True,
            'message': 'Cancelled Admit Request!'
        }
    )


@api_view(['POST'])
@check_blacklisted_token
def coworker_submit_request(request):
    jsn = request.data
    user = request.user
    if not user.is_authenticated:
        return Response(
            {
                'status': False,
                'messaage': 'Not logged in!'
            }
        )
    if 'hid' not in jsn:
        return Response(
            {
                'status': False,
                'message': 'Missing data in request'
            }
        )
    hospital = Hospital.objects.filter(id=jsn['hid']).first()
    if not hospital:
        return Response(
            {
                'status': False,
                'message': 'Requested hospital does not exists anymore!'
            }
        )
    if user.account_type not in [4, 5, 6]:
        return Response(
            {
                'status': False,
                'message': 'This feature is only for CoWorkers!'
            }
        )
    coworker = user.coworker
    if not coworker.available:
        return Response(
            {
                'status': False,
                'message': 'Unavailable CoWorker can not submit work request!'
            }
        )
    if coworker.work_request:
        return Response(
            {
                'status': False,
                'message': 'CoWorker can not send another work request while previous one is pending!'
            }
        )
    if coworker.id.account_type == 4:
        if not hospital.accepting_coworkers:
            return Response(
                {
                    'status': False,
                    'message': 'Requested hospital is not accepting any CoWorker!'
                }
            )
        if hospital.workers_requirement == 0:
            return Response(
                {
                    'status': False,
                    'message': 'Requested hospital does not require any more CoWorkers'
                }
            )
    elif coworker.id.account_type == 5:
        if not hospital.accepting_doctors:
            return Response(
                {
                    'status': False,
                    'message': 'Requested hospital is not accepting any Doctors!'
                }
            )
        if hospital.doctors_requirement == 0:
            return Response(
                {
                    'status': False,
                    'message': 'Requested hospital does not require any more Doctors'
                }
            )
    else:
        if not hospital.accepting_doctors:
            return Response(
                {
                    'status': False,
                    'message': 'Requested hospital is not accepting any Nurses!'
                }
            )
        if hospital.doctors_requirement == 0:
            return Response(
                {
                    'status': False,
                    'message': 'Requested hospital does not require any more Nurses'
                }
            )
    coworker.work_request = True
    coworker.requested_hospital = hospital
    coworker.save()
    return Response(
        {
            'status': True,
            'message': 'Request successfully submitted'
        }
    )


@api_view(['POST'])
@check_blacklisted_token
def coworker_cancel_request(request):
    user = request.user
    if not user.is_authenticated:
        return Response(
            {
                'status': False,
                'message': 'Not logged in'
            }
        )
    if user.account_type not in [4, 5, 6]:
        return Response(
            {
                'status': False,
                'message': 'This feature is only for CoWorkers!'
            }
        )
    coworker = user.coworker
    if not coworker.work_request:
        return Response(
            {
                'status': False,
                'message': 'There is no work request available to cancel!'
            }
        )
    coworker.work_request = False
    coworker.requested_hospital = None
    coworker.save()
    return Response(
        {
            'status': True,
            'message': 'Work Request Cancelled!'
        }
    )


@api_view(['POST'])
@check_blacklisted_token
def response_coworker_request(request):
    user = request.user
    if not user.is_authenticated:
        return Response(
            {
                'status': False,
                'message': 'Not logged in'
            }
        )
    if user.account_type != 2:
        return Response(
            {
                'status': False,
                'message': 'This feature is only for hospitals'
            }
        )
    jsn = request.data
    if ('accept' not in jsn) or not ('cid' in jsn and type(jsn['cid']) == int):
        return Response(
            {
                'status': False,
                'message': 'Missing data in request'
            }
        )
    cid = jsn['cid']
    coworker = CoWorker.objects.filter(id=cid).first()
    hospital = user.hospital
    if not coworker:
        return Response(
            {
                'status': False,
                'message': 'CoWorker does not exists!'
            }
        )
    if jsn['accept']:
        coworker.work_request = False
        coworker.requested_hospital = None
        coworker.available = False
        coworker.working_at = hospital
        coworker.save()
        if coworker.id.account_type == 4 and hospital.workers_requirement > 0:
            hospital.workers_requirement -= 1
            hospital.save()
        elif coworker.id.account_type == 5 and hospital.doctors_requirement > 0:
            hospital.doctors_requirement -= 1
            hospital.save()
        elif coworker.id.account_type == 6 and hospital.nurses_requirement > 0:
            hospital.nurses_requirement -= 1
            hospital.save()
        return Response(
            {
                'status': True,
                'message': "Co-Worker's request Successfully Accepted!"
            }
        )
    else:
        coworker.requested_hospital = None
        coworker.work_request = False
        coworker.save()
        return Response(
            {
                'status': True,
                'message': "Co-Worker's request declined!"
            }
        )


@api_view(['POST'])
@check_blacklisted_token
def remove_worker(request):
    jsn = request.data
    user = request.user
    if not user.is_authenticated:
        return Response(
            {
                'status': False,
                'message': 'Not logged in'
            }
        )
    if user.account_type != 2:
        return Response(
            {
                'status': False,
                'message': 'This feature is only for hospitals'
            }
        )
    if 'cid' not in jsn:
        return Response(
            {
                'status': False,
                'message': 'Missing data in request'
            }
        )
    hospital = user.hospital
    coworker = CoWorker.objects.filter(id=jsn['cid']).first()
    if not coworker:
        return Response(
            {
                'status': False,
                'message': 'requested coworker does not exists any more!'
            }
        )
    coworker.available = True
    coworker.working_at = None
    coworker.save()
    if coworker.id.account_type == 4 and hospital.accepting_coworkers:
        hospital.workers_requirement += 1
        hospital.save()
    elif coworker.id.account_type == 5 and hospital.accepting_doctors:
        hospital.doctors_requirement += 1
        hospital.save()
    elif coworker.id.account_type == 6 and hospital.accepting_nurses:
        hospital.nurses_requirement += 1
        hospital.save()
    return Response(
        {
            'status': True,
            'message': 'CoWorker removed!'
        }
    )


@api_view(['GET'])
@check_blacklisted_token
def get_coworkers(request):
    user = request.user
    if not user.is_authenticated:
        return Response(
            {
                'status': False,
                'message': 'Not logged in'
            }
        )
    if user.account_type != 2:
        return Response(
            {
                'status': False,
                'message': 'This feature is only for Hospitals!'
            }
        )
    hospital = user.hospital
    requests = hospital.coworker_requested_hospital
    coworkers_list = []
    for coworker in requests.all():
        ser_coworker = CoWorkerSerializer(coworker).data
        ser_coworker.update(UserSerializer(User.objects.filter(id=ser_coworker['id']).first()).data)
        coworkers_list.append(ser_coworker)
    return Response(
        {
            'status': True,
            'coworkers': coworkers_list
        }
    )


@api_view(['GET'])
@check_blacklisted_token
def get_working_coworkers(request):
    user = request.user
    if not user.is_authenticated:
        return Response(
            {
                'status': False,
                'message': 'Not logged in'
            }
        )
    if user.account_type != 2:
        return Response(
            {
                'status': False,
                'message': 'This feature is only for Hospitals!'
            }
        )
    hospital = user.hospital
    requests = hospital.coworker_working_at
    coworkers_list = []
    for coworker in requests.all():
        ser_coworker = CoWorkerSerializer(coworker).data
        ser_coworker.update(UserSerializer(User.objects.filter(id=ser_coworker['id']).first()).data)
        coworkers_list.append(ser_coworker)
    return Response(
        {
            'status': True,
            'coworkers': coworkers_list
        }
    )
