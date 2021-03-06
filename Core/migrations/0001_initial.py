# Generated by Django 2.2.1 on 2019-05-06 10:28

from django.db import migrations, models

import Core.models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ProjectModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tag', models.CharField(
                    choices=[('default', 'default'), ('home', 'home'), ('abroad', 'abroad'), ('other', 'other')],
                    default='other', max_length=50)),
                ('name', models.CharField(blank=True, max_length=100, null=True)),
                ('desc', models.TextField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='SettingModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('activating', models.BooleanField(default=False)),
                ('tag', models.CharField(
                    choices=[('debug', 'debug'), ('home', 'home'), ('abroad', 'abroad'), ('other', 'other')],
                    default='other', max_length=50)),
                ('kind', models.CharField(choices=[('redis', 'redis'), ('nginx_file_server', 'nginx_file_server')],
                                          default='other', max_length=50)),
                ('setting', Core.models.DiyDictField(default={})),
            ],
        ),
        migrations.CreateModel(
            name='TaskModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pid', models.IntegerField(default=0)),
                ('kind', models.CharField(blank=True, default=None, max_length=100, null=True)),
                ('kwargs', Core.models.DiyDictField(default={})),
                ('task_id', models.CharField(blank=True, default=None, max_length=150, null=True)),
                ('status', models.CharField(blank=True, choices=[('PENDING', 'PENDING'), ('STARTED', 'STARTED'),
                                                                 ('SUCCESS', 'SUCCESS'), ('FAILURE', 'FAILURE'),
                                                                 ('RETRY', 'RETRY'), ('REVOKED', 'REVOKED'),
                                                                 ('PROGRESS', 'PROGRESS'), ('STORED', 'STORED'),
                                                                 ('STOREFAIL', 'STOREFAIL')], default='PENDING',
                                            max_length=50, null=True)),
                ('start_time', models.IntegerField(default=0)),
                ('end_time', models.IntegerField(default=0)),
            ],
        ),
    ]
