from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Fix admin user permissions'

    def handle(self, *args, **options):
        try:
            user = User.objects.get(username='kouya828828')
            user.is_staff = True
            user.is_superuser = True
            user.save()
            self.stdout.write(self.style.SUCCESS(f'✅ User {user.username} updated successfully'))
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR('❌ User kouya828828 not found'))