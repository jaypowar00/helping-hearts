from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils import timezone
from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20)
    address = models.CharField(max_length=200, null=True)
    pincode = models.CharField(max_length=6, null=True, default=None)
    about = models.TextField(null=True, default=None)
    is_staff = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    account_type = models.PositiveIntegerField(default=1)
    date_joined = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    objects = UserManager()

    def __str__(self):
        return self.email


class Hospital(models.Model):
    id = models.OneToOneField(User, primary_key=True, on_delete=models.CASCADE)
    corona_count = models.IntegerField(default=0)
    beds = models.IntegerField(default=0)
    ventilators = models.IntegerField(default=0)
    oxygens = models.IntegerField(default=0)
    accepting_patients = models.BooleanField(default=True)
    accepting_coworkers = models.BooleanField(default=True)
    accepting_doctors = models.BooleanField(default=True)
    accepting_nurses = models.BooleanField(default=True)
    need_ventilator = models.BooleanField(default=False)
    ventilators_requirement = models.IntegerField(default=0)
    workers_requirement = models.IntegerField(default=0)
    doctors_requirement = models.IntegerField(default=0)
    nurses_requirement = models.IntegerField(default=0)


class VenProvider(models.Model):
    id = models.OneToOneField(User, primary_key=True, on_delete=models.CASCADE)
    age = models.IntegerField(null=True, default=None)
    gender = models.CharField(max_length=12, null=True, default=None)
    ventilators_available = models.BooleanField(default=True)
    total_ventilators = models.IntegerField(default=0)


class CoWorker(models.Model):
    id = models.OneToOneField(User, primary_key=True, on_delete=models.CASCADE)
    age = models.IntegerField(null=True, default=None)
    gender = models.CharField(max_length=12, null=True, default=None)
    available = models.BooleanField(default=True)
    working_at = models.OneToOneField(Hospital, null=True, default=None, on_delete=models.DO_NOTHING)


class Patient(models.Model):
    id = models.OneToOneField(User, primary_key=True, on_delete=models.CASCADE)
    age = models.IntegerField(null=True, default=None)
    gender = models.CharField(max_length=12, null=True, default=None)
    health_status = models.TextField(null=True, default=None)
    ct_scan_score = models.FloatField(null=True, default=None)
    ct_scan_document = models.TextField(null=True, default=None)
