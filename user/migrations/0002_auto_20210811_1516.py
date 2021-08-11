# Generated by Django 3.2.3 on 2021-08-11 09:46

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='coworker',
            name='requested_hospital',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='coworker_requested_hospital', to='user.hospital'),
        ),
        migrations.AlterField(
            model_name='coworker',
            name='working_at',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='coworker_working_at', to='user.hospital'),
        ),
        migrations.AlterField(
            model_name='patient',
            name='admitted_hospital',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='patient_admitted_hospital', to='user.hospital'),
        ),
        migrations.AlterField(
            model_name='patient',
            name='requested_hospital',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='patient_requested_hospital', to='user.hospital'),
        ),
    ]
