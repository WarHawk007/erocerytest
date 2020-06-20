# Generated by Django 2.2.6 on 2020-04-16 10:30

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0042_user_is_rider'),
        ('rider', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='riderid',
            field=models.OneToOneField(blank=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='admin_rider', to='rider.Rider'),
        ),
    ]
