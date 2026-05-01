from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.contrib.auth import get_user_model
import os

class Command(BaseCommand):
    help = 'Runs migrations and creates a superuser if it does not exist.'

    def handle(self, *args, **options):
        self.stdout.write("Running migrations...")
        call_command('migrate', interactive=False)

        self.stdout.write("Creating superuser...")
        User = get_user_model()
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@ssa.com')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin123!')

        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(username, email, password)
            self.stdout.write(self.style.SUCCESS(f"Superuser created successfully: {username} / {password}"))
        else:
            self.stdout.write(self.style.WARNING(f"Superuser '{username}' already exists."))
