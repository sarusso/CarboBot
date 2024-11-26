from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from ...models import Food, FoodObservation

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


        #=====================
        #  Demo Food
        #=====================
        foods = Food.objects.all()
        if foods:
            print('Not creating demo foods as they already exists')
        else:
            demo_foods = [
                { "uuid": "00000000-0000-0000-0000-000000000001", "cho_ratio": 0.01, "name": "Insalata caprese", "main_ingredients": ["mozzarella", "pomodoro", "basilico"]},
                { "uuid": "00000000-0000-0000-0000-000000000002", "cho_ratio": 0.35, "name": "Insalata di riso con verdure", "main_ingredients": ["riso", "carote", "piselli"]},
                { "uuid": "00000000-0000-0000-0000-000000000003", "cho_ratio": 0.35, "name": "Insalata di riso con pollo", "main_ingredients": ["riso", "pollo", "maionese"]},
                { "uuid": "00000000-0000-0000-0000-000000000004", "cho_ratio": 0.35, "name": "Insalata di riso con sottaceti vari", "main_ingredients": ["riso", "sottaceti", "olio"]},
                { "uuid": "00000000-0000-0000-0000-000000000038", "cho_ratio": 0.55, "name": "Arancini di riso", "main_ingredients": ["riso", "carne", "piselli"]}]
            for demo_food in demo_foods:
                food = Food(uuid = demo_food['uuid'],
                            name = demo_food['name'],
                            main_ingredients = demo_food['main_ingredients'],
                            created_by = testuser)
                food.save()

                # Create also some demo observations
                FoodObservation.objects.create(food = food,
                                               cho_ratio = demo_food['cho_ratio'],
                                               created_by = testuser)

            print('Added demo foods')











