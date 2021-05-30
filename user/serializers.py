from rest_framework import serializers
from .models import User, Hospital, CoWorker, Patient, VenProvider


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'name', 'phone', 'address', 'pincode', 'account_type', 'about', 'date_joined']


class HospitalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hospital
        fields = ['id', 'corona_count', 'beds', 'ventilators', 'oxygens', 'accepting_patients', 'accepting_coworkers',
                  'accepting_doctors', 'accepting_nurses', 'need_ventilator', 'ventilators_requirement',
                  'workers_requirement', 'doctors_requirement', 'nurses_requirement']


class CoWorkerSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoWorker
        fields = ['id', 'age', 'gender', 'available', 'working_at']


class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ['id', 'age', 'gender', 'health_status', 'ct_scan_score', 'ct_scan_document']


class VenProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = VenProvider
        fields = ['id', 'age', 'gender', 'ventilators_available', 'total_ventilators']
