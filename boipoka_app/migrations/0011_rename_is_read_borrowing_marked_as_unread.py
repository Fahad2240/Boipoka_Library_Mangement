# Generated by Django 5.1.1 on 2024-10-11 16:54

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('boipoka_app', '0010_borrowing_is_read'),
    ]

    operations = [
        migrations.RenameField(
            model_name='borrowing',
            old_name='is_read',
            new_name='marked_as_unread',
        ),
    ]