# Generated by Django 5.1.6 on 2025-04-01 05:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finance_tracker', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='account',
            name='institution_number',
            field=models.CharField(default='00000', max_length=10),
        ),
        migrations.AlterField(
            model_name='account',
            name='transit_number',
            field=models.CharField(default='00000', max_length=10),
        ),
    ]
