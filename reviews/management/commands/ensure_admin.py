from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from decouple import config

class Command(BaseCommand):
    help = 'Ensure admin user exists'

    def handle(self, *args, **options):
        username = config('ADMIN_USERNAME', default='admin')
        email = config('ADMIN_EMAIL', default='admin@gapmovies.com')
        password = config('ADMIN_PASSWORD', default='')
        
        if not password:
            self.stdout.write(self.style.ERROR('❌ ADMIN_PASSWORD環境変数が設定されていません'))
            return
        
        if User.objects.filter(username=username).exists():
            user = User.objects.get(username=username)
            user.is_staff = True
            user.is_superuser = True
            user.set_password(password)  # パスワードを更新
            user.save()
            self.stdout.write(self.style.SUCCESS(f'✅ Admin user updated'))
        else:
            User.objects.create_superuser(username, email, password)
            self.stdout.write(self.style.SUCCESS(f'✅ Admin user created'))