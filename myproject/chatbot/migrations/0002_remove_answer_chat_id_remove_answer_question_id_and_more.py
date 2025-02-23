# Generated by Django 5.1.1 on 2024-11-05 03:22

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chatbot', '0001_initial'),
        ('myapp', '0003_remove_profile_id_alter_profile_user'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='answer',
            name='chat_id',
        ),
        migrations.RemoveField(
            model_name='answer',
            name='question_id',
        ),
        migrations.RemoveField(
            model_name='answer',
            name='user_id',
        ),
        migrations.RemoveField(
            model_name='question',
            name='chat_id',
        ),
        migrations.RemoveField(
            model_name='question',
            name='user_id',
        ),
        migrations.RemoveField(
            model_name='webchatlist',
            name='user_id',
        ),
        migrations.AddField(
            model_name='answer',
            name='chat',
            field=models.ForeignKey(db_column='chat_id', null=True, on_delete=django.db.models.deletion.CASCADE, to='chatbot.webchatlist'),
        ),
        migrations.AddField(
            model_name='answer',
            name='question',
            field=models.ForeignKey(db_column='question_id', null=True, on_delete=django.db.models.deletion.CASCADE, to='chatbot.question'),
        ),
        migrations.AddField(
            model_name='answer',
            name='user',
            field=models.ForeignKey(blank=True, db_column='user_id', null=True, on_delete=django.db.models.deletion.CASCADE, to='myapp.profile'),
        ),
        migrations.AddField(
            model_name='question',
            name='chat',
            field=models.ForeignKey(db_column='chat_id', null=True, on_delete=django.db.models.deletion.CASCADE, to='chatbot.webchatlist'),
        ),
        migrations.AddField(
            model_name='question',
            name='user',
            field=models.ForeignKey(blank=True, db_column='user_id', null=True, on_delete=django.db.models.deletion.CASCADE, to='myapp.profile'),
        ),
        migrations.AddField(
            model_name='webchatlist',
            name='session_id',
            field=models.CharField(blank=True, max_length=40, null=True),
        ),
        migrations.AddField(
            model_name='webchatlist',
            name='user',
            field=models.ForeignKey(blank=True, db_column='user_id', null=True, on_delete=django.db.models.deletion.CASCADE, to='myapp.profile'),
        ),
        migrations.AlterField(
            model_name='webchatlist',
            name='chat_last_timestamp',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
