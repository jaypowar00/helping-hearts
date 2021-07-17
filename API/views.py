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
                hospitals = Hospital.objects.order_by(order+'id__name')
            elif orderby == 'pin':
                hospitals = Hospital.objects.order_by(order+'id__pincode')
            elif orderby == 'bed':
                hospitals = Hospital.objects.order_by(order+'beds')
            elif orderby == 'ven':
                hospitals = Hospital.objects.order_by(order+'ventilators')
            elif orderby == 'pox':
                hospitals = Hospital.objects.order_by(order+'oxygens')
    if len(hospitals) == 0:
        return Response(
            {
                'status': False,
                'message': 'there are no hospitals'
            }
        )
    serialized_hospitals = HospitalSerializer(hospitals, many=True).data
    paginator = Paginator(serialized_hospitals, 30)
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
            }
        )
    hid = query_params['hid']
    hospital = Hospital.objects.filter(id=hid).first()
    if not hospital:
        return Response(
            {
                'status': False,
                'message': 'Hospital does not exists!'
            }
        )
    serialized_hospital = HospitalSerializer(hospital).data
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
        return Response({
            'status': False,
            'message': 'Not logged in',
        })
    user = UserModel.objects.filter(id=user.id).first()
    if user is None:
        return Response(
            {
                'status': False,
                'message': 'user associated with credentials does not exists anymore',
            }
        )
    if user.account_type == 2:
        v_list = []
        venProviders = VenProvider.objects.all()
        for venProvider in venProviders:
            temp = VenProviderSerializer(venProvider).data
            temp.update(UserSerializer(venProvider.id).data)
            v_list.append(temp)
        # serialized_ventilator = VenProviderSerializer(venProvider, many=True).data
        # print(serialized_ventilator)
        return Response({
            'status': True,
            'Ventilator_Providers': v_list
        })
    else:
        return Response({
            'status': False,
            'message': 'Only accessible for the hospitals'
        })


@api_view(['GET'])
def get_co_workers(request):
    query_params = dict(request.query_params)
    UserModel = get_user_model()
    user = request.user
    if not user.is_authenticated:
        return Response({
            'status': False,
            'message': 'Not logged in',
        })
    user = UserModel.objects.filter(id=user.id).first()
    if user is None:
        return Response(
            {
                'status': False,
                'message': 'user associated with credentials does not exists anymore',
            }
        )

    if user.account_type == 2:
        coWorkers_list = []
        coWork = CoWorker.objects.all()
        for coWorker in coWork:
            temp = CoWorkerSerializer(coWork).data
            temp.update(UserSerializer(coWorker.id).data)
            coWorkers_list.append(temp)

        return Response({
            'status': True,
            'co_workers': coWorkers_list
        })
    else:
        return Response({
            'status': False,
            'message': 'Only accessible for Hospitals'
        })
