import jwt
import json
from django.conf import settings
from HelpingHearts.settings import blackListedTokens
from django.db.utils import IntegrityError
# from django.middleware.csrf import get_token
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model
from .serializers import UserSerializer, HospitalSerializer, VenProviderSerializer, PatientSerializer, CoWorkerSerializer
from .utils import generate_access_token, generate_refresh_token
from .decorators import check_blacklisted_token
from .models import User, Patient, VenProvider, CoWorker, Hospital


@api_view(['GET'])
@check_blacklisted_token
def user_profile(request):
    user = request.user
    try:
        serialized_user = UserSerializer(user).data
        ac_type = serialized_user['account_type']
        if ac_type == 1:
            patient = Patient.objects.filter(id=user.id).first()
            serialized_patient = PatientSerializer(patient).data
            del serialized_patient['id']
            serialized_user['account_type'] = 'patient'
            serialized_user['detail'] = serialized_patient
        if ac_type == 2:
            hospital = Hospital.objects.filter(id=user.id).first()
            serialized_hospital = HospitalSerializer(hospital).data
            del serialized_hospital['id']
            serialized_user['account_type'] = 'hospital'
            serialized_user['detail'] = serialized_hospital
        if ac_type == 3:
            ven_provider = VenProvider.objects.filter(id=user.id).first()
            serialized_ven_provider = VenProviderSerializer(ven_provider).data
            del serialized_ven_provider['id']
            serialized_user['account_type'] = 'ventilator provider'
            serialized_user['detail'] = serialized_ven_provider
        if 4 <= ac_type <= 6:
            coworker = CoWorker.objects.filter(id=user.id).first()
            serialized_coworker = CoWorkerSerializer(coworker).data
            del serialized_coworker['id']
            serialized_user['account_type'] = 'coworker' if ac_type == 4 else 'doctor' if ac_type == 5 else 'nurse'
            serialized_user['detail'] = serialized_coworker
    except AttributeError:
        return Response(
            {
                'response': 'Authorization Credentials missing!',
                'status': False
            }
        )
    return Response(
        {
            'status': True,
            'user': serialized_user
        }
    )


@api_view(['POST'])
@permission_classes([AllowAny])
def user_register(request):
    context = {}
    js: dict
    try:
        jsn = json.loads(request.body)
    except json.decoder.JSONDecodeError:
        jsn = {}
    if jsn:
        for key, value in jsn.items():
            if key != 'password':
                context[key] = value
    if not ('email' in jsn and 'username' in jsn and 'password' in jsn and 'name' in jsn and
            'phone' in jsn and 'address' in jsn and 'account_type' in jsn):
        return Response(
            {
                'status': False,
                'message': 'registration unsuccessful (required data: name, email, username, password, phone, address, account_type)'
            }
        )
    try:
        UserModel = get_user_model()
        user = UserModel(
            email=jsn['email'],
            username=jsn['username'],
            name=jsn['name'],
            phone=jsn['phone'],
            address=jsn['address'],
            account_type=jsn['account_type']
        )
        user.set_password(jsn['password'])
        user.save()
        if jsn['account_type'] == 1:
            age = gender = diseases = None
            if 'age' in jsn:
                age = jsn['age']
            if 'gender' in jsn:
                gender = jsn['gender']
            if 'diseases' in jsn:
                diseases = jsn['diseases']
            patient = Patient(user.id, age=age, gender=gender, health_status=diseases)
            patient.save()
        elif jsn['account_type'] == 2:
            c_count = beds = ventilators = oxygens = n_doctors = n_coworkers = n_nurses = n_ventilators = 0
            a_patients = a_coworkers = a_doctors = a_nurses = a_ventitalors = False
            if 'c_count' in jsn:
                c_count = jsn['c_count']
            if 'beds' in jsn:
                beds = jsn['beds']
            if 'ventilators' in jsn:
                ventilators = jsn['ventilators']
            if 'oxygens' in jsn:
                oxygens = jsn['oxygens']
            if 'accepting_patients' in jsn:
                a_patients = jsn['accepting_patients']
            if 'accepting_coworkers' in jsn:
                a_coworkers = jsn['accepting_coworkers']
            if 'accepting_doctors' in jsn:
                a_doctors = jsn['accepting_doctors']
            if 'accepting_nurses' in jsn:
                a_nurses = jsn['accepting_nurses']
            if 'need_ventilators' in jsn:
                a_ventitalors = jsn['need_ventilators']
            if 'ventilators_required' in jsn:
                n_ventilators = jsn['ventilators_required']
            if 'doctors_required' in jsn:
                n_doctors = jsn['doctors_required']
            if 'nurses_required' in jsn:
                n_nurses = jsn['nurses_required']
            if 'coworkers_required' in jsn:
                n_coworkers = jsn['coworkers_required']
            hospital = Hospital(user.id, c_count, beds, ventilators, oxygens, a_patients, a_coworkers, a_doctors,
                                a_nurses, a_ventitalors, n_ventilators, n_coworkers, n_doctors, n_nurses)
            hospital.save()
        elif jsn['account_type'] == 3:
            age = gender = None
            ven_avail = False
            total_ven = 0
            if 'age' in jsn:
                age = jsn['age']
            if 'gender' in jsn:
                gender = jsn['gender']
            if 'ven_avail' in jsn:
                ven_avail = jsn['ven_avail']
            if 'total_ven' in jsn:
                total_ven = jsn['total_ven']
            venProvider = VenProvider(user.id, age, gender, ven_avail, total_ven)
            venProvider.save()
        elif 4 <= jsn['account_type'] <= 6:
            age = gender = None
            available = True
            working_at = None
            if 'age' in jsn:
                age = jsn['age']
            if 'gender' in jsn:
                gender = jsn['gender']
            if 'available' in jsn:
                available = jsn['available']
            if 'working_at' in jsn:
                hospital = Hospital.objects.filter(id=jsn['working_at']).first()
                if hospital:
                    working_at = hospital
            coworker = CoWorker(user.id, age, gender, available, working_at)
            coworker.save()
    except IntegrityError as err:
        print(str(err))
        dup = str(err).split('user_user')[1].split('.')[1]
        return Response(
            {
                'status': False,
                'message': f'{dup} already taken by another user, try again with another {dup}',
                'duplicate': dup
            }
        )
    except IndexError:
        return Response(
            {
                'status': False,
                'message': 'Duplication Found!'
            }
        )
    if jsn:
        return Response(
            {
                'status': True,
                'message': 'User created!',
                'user': context
            }
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def user_login(request):
    UserModel = get_user_model()
    email = request.data.get('email')
    password = request.data.get('password')
    response = Response()
    if email is None or password is None:
        return Response(
            {
                'status': False,
                'message': 'email/password fields missing!',
            }
        )
    user = UserModel.objects.filter(email=email).first()
    if user is None:
        return Response(
            {
                'status': False,
                'message': 'User not found!',
            }
        )
    if not user.check_password(password):
        return Response(
            {
                'status': False,
                'message': 'Wrong password',
            }
        )

    serialized_user = UserSerializer(user).data
    access_token = generate_access_token(user)
    refresh_token = generate_refresh_token(user)
    # csrf_token = get_token(request)
    response.set_cookie(key='refreshtoken', value=refresh_token, httponly=True, secure=True, samesite=None)
    response.data = {
        'status': True,
        'message': 'successfully logged in',
        'access_token': access_token,
        # 'refresh_token': refresh_token,
        # 'csrf_token': csrf_token,
        'user': serialized_user,
    }
    return response


@api_view(['POST'])
def user_logout(request):
    UserModel = get_user_model()
    authorization_header = request.headers.get('Authorization')
    if not authorization_header:
        return Response(
            {
                'status': False,
                'message': 'Authorization credential missing!',
            }
        )
    access_token = False
    refresh_token = False
    try:
        access_token = authorization_header.split(' ')[1]
        refresh_token = request.COOKIES.get('refreshtoken')
        payload = jwt.decode(access_token, settings.SECRET_KEY, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        if not refresh_token:
            return Response(
                {
                    'status': True,
                    'message': 'Some Credentials not found in request. (might have already been logged out)',
                }
            )
        try:
            payload = jwt.decode(refresh_token, settings.REFRESH_SECRET_KEY, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return Response(
                {
                    'status': True,
                    'message': 'jwt session has already been timed out. (have been already logged out)',
                }
            )
        user = UserModel.objects.filter(id=payload['user.id']).first()
        if user is None:
            return Response(
                {
                    'status': True,
                    'message': 'user associated with credentials does not exists anymore',
                }
            )
    finally:
        if access_token in blackListedTokens and refresh_token in blackListedTokens:
            return Response(
                {
                    'status': True,
                    'message': 'already logged out!',
                }
            )
        if access_token in blackListedTokens:
            if refresh_token:
                blackListedTokens.add(refresh_token)
            return Response(
                {
                    'status': True,
                    'message': 'already logged out!',
                }
            )
        if refresh_token in blackListedTokens:
            if access_token:
                blackListedTokens.add(access_token)
            return Response(
                {
                    'status': True,
                    'message': 'already logged out!',
                }
            )
        if access_token:
            blackListedTokens.add(access_token)
        if refresh_token:
            blackListedTokens.add(refresh_token)
    return Response(
        {
            'status': True,
            'message': 'successfully logged out!',
        }
    )


@api_view(['POST'])
@check_blacklisted_token
def refresh_token_view(request):
    UserModel = get_user_model()
    refresh_token = request.COOKIES.get('refreshtoken')
    if not refresh_token:
        return Response(
            {
                'status': False,
                'message': 'refresh token missing in cookies',
            }
        )
    try:
        payload = jwt.decode(refresh_token, settings.REFRESH_SECRET_KEY, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        return Response(
            {
                'status': False,
                'message': 'refresh token expired!',
            }
        )
    except jwt.InvalidSignatureError or jwt.DecodeError:
        return Response(
            {
                'status': False,
                'message': 'invalid refresh token!',
            }
        )
    user = UserModel.objects.filter(id=payload['user.id']).first()
    if user is None:
        return Response(
            {
                'status': False,
                'message': 'user associated with received refresh token does not exists anymore!',
            }
        )
    access_token = generate_access_token(user)
    # csrf_token = get_token(request)
    return Response(
        {
            'status': True,
            'message': 'access token refreshed',
            'access_token': access_token,
            # 'csrf_token': csrf_token,
        }
    )


@api_view(['POST'])
@check_blacklisted_token
def user_delete(request):
    UserModel = get_user_model()
    authorization_header = request.headers.get('Authorization')
    if not authorization_header:
        return Response(
            {
                'status': False,
                'message': 'authorization credential missing in request!',
            }
        )
    try:
        access_token = authorization_header.split(' ')[1]
        payload = jwt.decode(access_token, settings.SECRET_KEY, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        return Response(
            {
                'status': False,
                'message': 'access token expired!',
            }
        )
    user = UserModel.objects.filter(id=payload['user_id']).first()
    if user is None:
        return Response(
            {
                'status': False,
                'message': 'User not found!',
            }
        )
    user.delete()
    return Response(
        {
            'status': True,
            'message': 'User profile successfully deleted',
        }
    )


@api_view(['GET'])
@check_blacklisted_token
def user_verify(request):
    user = request.user
    response = {}
    try:
        serialized_user = UserSerializer(user).data
        ac_type = serialized_user['account_type']
        response['id'] = serialized_user['id']
        response['username'] = serialized_user['username']
        response['name'] = serialized_user['name']
        response['pincode'] = serialized_user['pincode']
        if ac_type == 1:
            response['account_type'] = 'patient'
        if ac_type == 2:
            response['account_type'] = 'hospital'
        if ac_type == 3:
            response['account_type'] = 'ventilator provider'
        if 4 <= ac_type <= 6:
            response['account_type'] = 'coworker' if ac_type == 4 else 'doctor' if ac_type == 5 else 'nurse'
    except AttributeError:
        return Response(
            {
                'status': False,
                'response': 'Authorization Credentials missing!'
            }
        )
    return Response(
        {
            'status': True,
            'user': response
        }
    )


@api_view(['POST'])
@check_blacklisted_token
def user_modify(request):
    user = request.user
    context = {}
    js: dict
    try:
        jsn = json.loads(request.body)
    except json.decoder.JSONDecodeError:
        jsn = {}
    if jsn:
        for key, value in jsn.items():
            if key != 'password' or key != 'new_password':
                context[key] = value
    if 'password' not in jsn:
        return Response(
            {
                'status': False,
                'message': 'password missing'
            }
        )
    try:
        UserModel = get_user_model()
        user = UserModel.objects.filter(id=user.id).first()
        if not user.check_password(jsn['password']):
            return Response(
                {
                    'status': False,
                    'message': 'wrong password'
                }
            )
        if 'new_password' in jsn:
            user.set_password(jsn['new_password'])
        user.name = jsn['name'] if 'name' in jsn else user.name
        user.phone = jsn['phone'] if 'phone' in jsn else user.phone
        user.address = jsn['address'] if 'address' in jsn else user.address
        user.pincode = jsn['pincode'] if 'pincode' in jsn else user.pincode
        user.about = jsn['about'] if 'about' in jsn else user.about
        user.save()
        if user.account_type == 1:
            patient = Patient.objects.filter(id=user.id).first()
            patient.age = jsn['age'] if 'age' in jsn else patient.age
            patient.gender = jsn['gender'] if 'gender' in jsn else patient.gender
            patient.health_status = jsn['diseases'] if 'diseases' in jsn else patient.health_status
            patient.save()
        elif user.account_type == 2:
            hospital = Hospital.objects.filter(id=user.id).first()
            hospital.corona_count = jsn['c_count'] if 'c_count' in jsn else hospital.corona_count
            hospital.beds = jsn['beds'] if 'beds' in jsn else hospital.beds
            hospital.ventilators = jsn['ventilators'] if 'ventilators' in jsn else hospital.ventilators
            hospital.oxygens = jsn['oxygens'] if 'oxygens' in jsn else hospital.oxygens
            hospital.accepting_patients = jsn['accepting_patients'] if 'accepting_patients' in jsn else hospital.accepting_patients
            hospital.accepting_coworkers = jsn['accepting_coworkers'] if 'accepting_coworkers' in jsn else hospital.accepting_coworkers
            hospital.accepting_doctors = jsn['accepting_doctors'] if 'accepting_doctors' in jsn else hospital.accepting_doctors
            hospital.accepting_nurses = jsn['accepting_nurses'] if 'accepting_nurses' in jsn else hospital.accepting_nurses
            hospital.need_ventilator = jsn['need_ventilators'] if 'need_ventilators' in jsn else hospital.need_ventilator
            hospital.ventilators_requirement = jsn['ventilators_required'] if 'ventilators_required' in jsn else hospital.ventilators_requirement
            hospital.doctors_requirement = jsn['doctors_required'] if 'doctors_required' in jsn else hospital.doctors_requirement
            hospital.nurses_requirement = jsn['nurses_required'] if 'nurses_required' in jsn else hospital.nurses_requirement
            hospital.workers_requirement = jsn['coworkers_required'] if 'coworkers_required' in jsn else hospital.workers_requirement
            hospital.save()
        elif user.account_type == 3:
            venProvider = VenProvider.objects.filter(id=user.id).first()
            venProvider.age = jsn['age'] if 'age' in jsn else venProvider.age
            venProvider.gender = jsn['gender'] if 'gender' in jsn else venProvider.gender
            venProvider.ventilators_available = jsn['ven_avail'] if 'ven_avail' in jsn else venProvider.ventilators_available
            venProvider.total_ventilators = jsn['total_ven'] if 'total_ven' in jsn else venProvider.total_ventilators
            venProvider.save()
        elif 4 <= user.account_type <= 6:
            coworker = CoWorker.objects.filter(id=user.id).first()
            coworker.age = jsn['age'] if 'age' in jsn else coworker.age
            coworker.gender = jsn['gender'] if 'gender' in jsn else coworker.gender
            coworker.available = jsn['available'] if 'available' in jsn else coworker.available
            if 'working_at' in jsn:
                if jsn['working_at'] is None:
                    working_at = None
                else:
                    hospital = Hospital.objects.filter(id=jsn['working_at']).first()
                    if hospital:
                        working_at = hospital
                coworker.working_at = working_at
            coworker.save()
    except Exception as e:
        return Response(
            {
                'status': False,
                'message': 'Server Error while Updating User'
            }
        )
    if jsn:
        return Response(
            {
                'status': True,
                'message': 'User updated!',
                'user': context
            }
        )
