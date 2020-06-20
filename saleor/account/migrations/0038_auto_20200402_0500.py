# Generated by Django 2.2.6 on 2020-04-02 10:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0037_auto_20200402_0154'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='phone_verified',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='user',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
    ]
