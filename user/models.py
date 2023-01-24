from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20, default=None, null=True, blank=True)
    address = models.CharField(max_length=200, null=True, blank=True)
    pincode = models.CharField(max_length=6, null=True, default=None, blank=True)
    about = models.TextField(null=True, default=None, blank=True)
    is_staff = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    account_type = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(6)])
    date_joined = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    objects = UserManager()

    def __str__(self):
        return self.email


class Hospital(models.Model):
    id = models.OneToOneField(User, primary_key=True, on_delete=models.CASCADE)
    corona_count = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    beds = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    ventilators = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    oxygens = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    accepting_patients = models.BooleanField(default=True)
    accepting_coworkers = models.BooleanField(default=True)
    accepting_doctors = models.BooleanField(default=True)
    accepting_nurses = models.BooleanField(default=True)
    need_ventilator = models.BooleanField(default=False)
    ventilators_requirement = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    workers_requirement = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    doctors_requirement = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    nurses_requirement = models.IntegerField(default=0, validators=[MinValueValidator(0)])

    def __unicode__(self):
        return self.id.email

    def __str__(self):
        return self.id.email


class VenProvider(models.Model):
    id = models.OneToOneField(User, primary_key=True, on_delete=models.CASCADE)
    age = models.IntegerField(null=True, default=None, blank=True)
    gender = models.CharField(max_length=12, null=True, default=None, blank=True)
    ventilators_available = models.BooleanField(default=True)
    total_ventilators = models.IntegerField(default=0, validators=[MinValueValidator(0)])

    def __unicode__(self):
        return self.id.email

    def __str__(self):
        return self.id.email


class CoWorker(models.Model):
    id = models.OneToOneField(User, primary_key=True, on_delete=models.CASCADE)
    age = models.IntegerField(null=True, default=None, blank=True)
    gender = models.CharField(max_length=12, null=True, default=None, blank=True)
    available = models.BooleanField(default=True)
    working_at = models.ForeignKey(Hospital, related_name='%(class)s_working_at', null=True, default=None, on_delete=models.SET_NULL, blank=True)
    work_request = models.BooleanField(default=False)
    requested_hospital = models.ForeignKey(Hospital, related_name='%(class)s_requested_hospital', null=True, default=None, on_delete=models.SET_NULL, blank=True)

    def __unicode__(self):
        return self.id.email

    def __str__(self):
        return self.id.email


class Patient(models.Model):
    id = models.OneToOneField(User, primary_key=True, on_delete=models.CASCADE)
    age = models.IntegerField(null=True, default=None, blank=True)
    gender = models.CharField(max_length=12, null=True, default=None, blank=True)
    health_status = models.TextField(null=True, default=None, blank=True)
    ct_scan_score = models.FloatField(null=True, default=None, blank=True)
    ct_scan_document = models.TextField(null=True, default=None, blank=True)
    admit_request = models.BooleanField(default=False)
    requested_hospital = models.ForeignKey(Hospital, related_name='%(class)s_requested_hospital', null=True, default=None, on_delete=models.SET_NULL, blank=True)
    admitted = models.BooleanField(default=False)
    admitted_hospital = models.ForeignKey(Hospital, related_name='%(class)s_admitted_hospital', null=True, default=None, on_delete=models.SET_NULL, blank=True)
    bed_type = models.IntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(3)])

    def __unicode__(self):
        return self.id.email

    def __str__(self):
        return self.id.email
