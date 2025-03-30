# Generated by Django 5.1.6 on 2025-03-30 04:14

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finance_tracker', '0002_account_account_number_account_institution_number_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Asset',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('asset_type', models.CharField(choices=[('Stock', 'Stock'), ('Real Estate', 'Real Estate'), ('Bond', 'Bond'), ('Other', 'Other')], max_length=50)),
                ('name', models.CharField(max_length=100)),
                ('current_value', models.DecimalField(decimal_places=2, max_digits=20)),
                ('last_updated', models.DateTimeField(default=django.utils.timezone.now)),
                ('account', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='finance_tracker.account')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='StockDetail',
            fields=[
                ('asset', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='finance_tracker.asset')),
                ('ticker', models.CharField(max_length=10, unique=True)),
                ('exchange', models.CharField(blank=True, max_length=20, null=True)),
                ('sector', models.CharField(blank=True, max_length=50, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='AssetHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.DecimalField(decimal_places=2, max_digits=20)),
                ('update_source', models.CharField(choices=[('User', 'User'), ('API', 'API')], max_length=50)),
                ('change_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('asset', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='finance_tracker.asset')),
            ],
        ),
        migrations.CreateModel(
            name='Debt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('debt_type', models.CharField(choices=[('Loan', 'Loan'), ('Credit Card', 'Credit Card'), ('Mortgage', 'Mortgage')], max_length=50)),
                ('name', models.CharField(max_length=100)),
                ('principal_amount', models.DecimalField(decimal_places=2, max_digits=20)),
                ('interest_type', models.CharField(choices=[('Fixed', 'Fixed'), ('Variable', 'Variable')], max_length=20)),
                ('interest_rate', models.DecimalField(decimal_places=2, max_digits=5)),
                ('payment_frequency', models.CharField(choices=[('Monthly', 'Monthly'), ('Quarterly', 'Quarterly'), ('Annual', 'Annual')], max_length=20)),
                ('remaining_balance', models.DecimalField(decimal_places=2, max_digits=20)),
                ('last_updated', models.DateField(default=django.utils.timezone.now)),
                ('account', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='finance_tracker.account')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='DebtHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('balance', models.DecimalField(decimal_places=2, max_digits=20)),
                ('interest_rate', models.DecimalField(decimal_places=2, max_digits=5)),
                ('update_source', models.CharField(choices=[('Bank', 'Bank'), ('User', 'User')], max_length=50)),
                ('change_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('debt', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='finance_tracker.debt')),
            ],
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount_paid', models.DecimalField(decimal_places=2, max_digits=20)),
                ('payment_date', models.DateField(default=django.utils.timezone.now)),
                ('remaining_balance', models.DecimalField(decimal_places=2, max_digits=20)),
                ('debt', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='finance_tracker.debt')),
            ],
        ),
    ]
