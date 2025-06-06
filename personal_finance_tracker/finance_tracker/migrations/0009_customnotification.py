# Generated by Django 5.1.6 on 2025-05-24 23:46

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finance_tracker', '0008_alter_budget_unique_together_remove_budget_name_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='CustomNotification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('generic', 'Generic'), ('purchase', 'Purchase Size'), ('balance', 'Account Balance'), ('budget', 'Budget Limit'), ('reminder', 'Reminder')], default='generic', max_length=20)),
                ('title', models.CharField(max_length=100)),
                ('message', models.TextField(max_length=512)),
                ('threshold', models.FloatField(blank=True, null=True)),
                ('enabled', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('category', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='finance_tracker.category')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
