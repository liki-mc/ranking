# Generated by Django 5.1.5 on 2025-01-23 18:27

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Ranking',
            fields=[
                ('name', models.CharField(max_length=200)),
                ('rid', models.IntegerField(primary_key=True, serialize=False)),
                ('character', models.CharField(max_length=200)),
                ('channel', models.IntegerField()),
                ('date', models.DateTimeField(auto_now_add=True, verbose_name='date published')),
            ],
        ),
        migrations.CreateModel(
            name='Entry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.IntegerField()),
                ('user', models.IntegerField()),
                ('date', models.DateTimeField(auto_now_add=True, verbose_name='date published')),
                ('ranking', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='website.ranking')),
            ],
        ),
    ]
