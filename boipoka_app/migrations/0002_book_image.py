# Generated by Django 5.1.1 on 2024-09-26 20:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('boipoka_app', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='book',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='book_images'),
        ),
    ]
