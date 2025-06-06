# Generated by Django 5.1.6 on 2025-05-26 00:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finance_tracker', '0009_customnotification'),
    ]

    operations = [
        migrations.AddField(
            model_name='customnotification',
            name='notification_datetime',
            field=models.DateTimeField(blank=True, help_text='Date and time for the notification to first occur (for Generic/Reminder types).', null=True),
        ),
        migrations.AddField(
            model_name='customnotification',
            name='recurrence_interval',
            field=models.CharField(blank=True, choices=[('NONE', 'Once (No Recurrence)'), ('DAILY', 'Daily'), ('WEEKLY', 'Weekly'), ('MONTHLY', 'Monthly')], default='NONE', help_text='How often the notification should repeat (for Generic/Reminder types).', max_length=10, null=True),
        ),
    ]
