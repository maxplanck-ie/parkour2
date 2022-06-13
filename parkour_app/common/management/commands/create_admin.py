from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()


class Command(BaseCommand):
    help = 'Create an admin user (if not exists) with password from env'

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, default='', dest='email',
                            help='admin email')
        parser.add_argument('--password', type=str, default='', dest='pass',
                            help='admin password')

    def handle(self, *args, **kwargs):
        admin_email = kwargs['email'] \
            if kwargs['email'] else settings.SETUP_ADMIN_EMAIL
        admin_password = kwargs['pass'] \
            if kwargs['pass'] else settings.SETUP_ADMIN_PASSWORD

        try:
            User.objects.create_user(
                'admin',
                admin_email,
                admin_password,
                is_staff=True,
                is_superuser=True,
            )
        except:
            pass
