# Generated by Django 5.1.5 on 2025-01-23 18:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ranking',
            name='rid',
            field=models.AutoField(primary_key=True, serialize=False),
        ),
    ]
