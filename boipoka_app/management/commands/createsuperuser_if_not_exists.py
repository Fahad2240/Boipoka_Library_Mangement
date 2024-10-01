from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Create a superuser if it does not exist'

    def handle(self, *args, **kwargs):
        User = get_user_model()
        if not User.objects.filter(is_superuser=True).exists():
            username = 'admin'  # Change this
            email = 'fahadish861@gmail.com'  # Change this
            password = 'admin'  # Change this
            User.objects.create_superuser(username=username, email=email, password=password)
            self.stdout.write(self.style.SUCCESS(f'Superuser {username} created'))
        else:
            self.stdout.write(self.style.SUCCESS('Superuser already exists'))
