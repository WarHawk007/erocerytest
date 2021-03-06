# Generated by Django 2.2.6 on 2020-04-16 10:48

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0043_user_riderid'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='riderid',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='admin_rider', to='rider.Rider'),
        ),
        migrations.AlterField(
            model_name='user',
            name='shopid',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='admin_subshop', to='subshop.SubShop'),
        ),
    ]
