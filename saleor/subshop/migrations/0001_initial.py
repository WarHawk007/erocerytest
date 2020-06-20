# Generated by Django 2.2.6 on 2020-04-14 09:37

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import saleor.core.utils.json_serializer


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='SubShop',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('private_meta', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=dict, encoder=saleor.core.utils.json_serializer.CustomJsonEncoder, null=True)),
                ('meta', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=dict, encoder=saleor.core.utils.json_serializer.CustomJsonEncoder, null=True)),
                ('name', models.CharField(max_length=128)),
                ('city', models.CharField(max_length=128)),
            ],
            options={
                'ordering': ('name',),
            },
        ),
    ]
