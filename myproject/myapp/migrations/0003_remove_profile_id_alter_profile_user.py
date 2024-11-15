# Generated by Django 5.1.1 on 2024-11-04 07:12

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0002_rename_deleted_time_profile_user_deleted_time_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveField(
            model_name='profile',
            name='id',
        ),
        migrations.AlterField(
            model_name='profile',
            name='user',
            field=models.OneToOneField(db_column='user_id', on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL),
        ),
    ]
