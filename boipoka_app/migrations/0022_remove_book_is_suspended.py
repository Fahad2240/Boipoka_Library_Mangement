# Generated by Django 5.1.1 on 2024-10-12 20:28

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('boipoka_app', '0021_subscription_marked_as_unread'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='book',
            name='is_suspended',
        ),
    ]
