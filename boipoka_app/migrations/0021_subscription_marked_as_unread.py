# Generated by Django 5.1.1 on 2024-10-12 19:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('boipoka_app', '0020_subscription_returneddash'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscription',
            name='marked_as_unread',
            field=models.BooleanField(default=False),
        ),
    ]