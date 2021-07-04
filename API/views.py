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
def get_hospitals_for_patients(request):
    query_params = dict(request.query_params)
    UserModel = get_user_model()
    authorization_header = request.headers.get('Authorization')
    if not authorization_header:
        response = retrieve_hospitals_for_patients(query_params)
        return response
    try:
        access_token = authorization_header.split(' ')[1]
        payload = jwt.decode(access_token, settings.SECRET_KEY, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        return Response(
            {
                'status': False,
                'message': 'session expired',
            }
        )
    user = UserModel.objects.filter(id=payload['user_id']).first()
    if user is None:
        return Response(
            {
                'status': False,
                'message': 'user associated with credentials does not exists anymore',
            }
        )
    if user.account_type == 1:
        return retrieve_hospitals_for_patients(query_params)
    elif user.account_type == 2:

        return Response({'success': True, 'message': 'Under development...'})
    elif user.account_type == 3:
        return Response({'success': True, 'message': 'Under development...'})
    elif user.account_type == 4:
        return Response({'success': True, 'message': 'Under development...'})
    elif user.account_type == 5:
        return Response({'success': True, 'message': 'Under development...'})
    else:
        return Response({'success': True, 'message': 'Under development...'})


def retrieve_hospitals_for_patients(query_params):
    hospitals = Hospital.objects.all()
    if len(hospitals) == 0:
        return Response(
            {
                'status': False,
                'message': 'there are no hospitals'
            }
        )
    serialized_hospitals = HospitalSerializer(hospitals, many=True).data
    paginator = Paginator(serialized_hospitals, 30)
    page_no = query_params['page'][0] if 'page' in query_params else 1
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
def get_venProviders(request):
    query_params = dict(request.query_params)

    venProvider = VenProvider.objects.all()
    serialized_ventilator = VenProviderSerializer(venProvider, many=True).data
    # print(serialized_ventilator)
    return Response(serialized_ventilator)
