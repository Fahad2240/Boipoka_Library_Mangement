# Generated by Django 5.1.1 on 2024-10-12 08:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('boipoka_app', '0016_subscription_is_active'),
    ]

    operations = [
        migrations.AddField(
            model_name='borrowing',
            name='damagedlostat',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='borrowing',
            name='fine_paid_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
