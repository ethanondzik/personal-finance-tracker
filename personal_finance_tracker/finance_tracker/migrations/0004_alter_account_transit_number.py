# Generated by Django 5.1.6 on 2025-03-30 05:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finance_tracker', '0003_asset_stockdetail_assethistory_debt_debthistory_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='account',
            name='transit_number',
            field=models.CharField(default=0, max_length=10),
        ),
    ]
