# Generated by Django 5.1.1 on 2024-10-11 14:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('boipoka_app', '0009_borrowing_reissue_state'),
    ]

    operations = [
        migrations.AddField(
            model_name='borrowing',
            name='is_read',
            field=models.BooleanField(default=False),
        ),
    ]
