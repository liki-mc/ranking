# Generated by Django 5.1.5 on 2025-01-24 19:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0005_ranking_active'),
    ]

    operations = [
        migrations.AlterField(
            model_name='entry',
            name='number',
            field=models.FloatField(default=1),
        ),
    ]
