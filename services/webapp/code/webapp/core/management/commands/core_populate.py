from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
# from ...models import Profile, Container, Computing, Storage, KeyPair, Page
#
class Command(BaseCommand):
    help = 'Adds the admin superuser with \'a\' password.'

    def handle(self, *args, **options):


        #=====================
        #  Testuser
        #=====================
        try:
            testuser = User.objects.get(username='testuser')
            print('Not creating test user as it already exists')

        except User.DoesNotExist:
            print('Creating test user with default password')
            testuser = User.objects.create_user('testuser', 'testuser@carbobot', 'testpass')
            print('Making testuser admin')
            testuser.is_staff = True
            testuser.is_admin=True
            testuser.is_superuser=True
            testuser.save() 
