# Generated by Django 2.2.6 on 2020-04-27 05:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rider', '0002_auto_20200421_0435'),
    ]

    operations = [
        migrations.AddField(
            model_name='rider',
            name='channel',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='rider',
            name='isonline',
            field=models.BooleanField(default=False),
        ),
    ]
