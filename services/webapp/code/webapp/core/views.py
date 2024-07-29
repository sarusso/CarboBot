from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotFound
from django.contrib.auth.models import User
from django.shortcuts import redirect
from .models import Food, FoodObservation
from .decorators import public_view, private_view
from .exceptions import ErrorMessage

# Setup logging
import logging
logger = logging.getLogger(__name__)


#=========================
#  User login view
#=========================

@public_view
def user_login(request):

    # If unauthenticated user tries to log in
    if request.method == 'POST':
        if not request.user.is_authenticated:
            username = request.POST.get('username')
            password = request.POST.get('password')

            if not username or not password:
                raise ErrorMessage('Empty username or password')

            user = authenticate(username=username, password=password)
            if user:
                login(request, user)
                return HttpResponseRedirect('/')
            else:
                raise ErrorMessage('Check username and password')

        else:
            # User tried to log-in while already logged in: log him out and then render the login (should never happen)
            logout(request)

    else:
        if request.user.is_authenticated:
            return HttpResponseRedirect('/')
        else:
            return render(request, 'login.html', {'data': {}})

@private_view
def user_logout(request):
    logout(request)
    return HttpResponseRedirect('/')


@private_view
def user_account(request):

    data={}
    data['user'] = request.user

    # Set values from POST and GET
    edit = request.POST.get('edit', None)
    if not edit:
        edit = request.GET.get('edit', None)
        data['edit'] = edit
    value = request.POST.get('value', None)

    # Fix None
    if value and value.upper() == 'NONE':
        value = None
    if edit and edit.upper() == 'NONE':
        edit = None

    # Do we have to edit something?
    if edit:
        try:
            logger.info('Editing "{}" with value "{}"'.format(edit,value))

            # Email
            if edit=='email' and value:
                request.user.email=value
                request.user.save()

            # Password
            elif edit=='password' and value:
                request.user.set_password(value)
                request.user.save()

            # Generic property
            elif edit and value:
                raise Exception('Unknown attribute "{}" to edit'.format(edit))

        except Exception as e:
            logger.error('Error in performing the "{}" operation:"{}"'.format(edit, e))
            data['error'] = 'Sorry, something unexpected happened. Please retry or contact support.'
            return render(request, 'error.html', {'data': data})

    return render(request, 'account.html', {'data': data})

@public_view
def entrypoint(request):
    return HttpResponseRedirect('/main/')


@public_view
def main(request):
    return render(request, 'main.html', {'data': {}})

@private_view
def food(request):
    if request.method == 'POST':
        query = request.POST.get('query', None)
        foods = Food.objects.filter(name__icontains=query)
    else:
        query = None
        foods = Food.objects.all()
    return render(request, 'food.html', {'data': {'foods': foods, 'query': query}})

@private_view
def food_add(request):
    data = {}
    if request.method == 'POST':
        name = request.POST.get('name', None)
        main_ingredients = request.POST.get('main_ingredients', None)
        typical_weight = request.POST.get('typical_weight', None)

        if not name:
            raise ErrorMessage('Food name is required')

        if not main:
            raise ErrorMessage('Food name is required')

        if typical_weight:
            try:
                typical_weigth = int(typical_weight)
            except:
                raise ErrorMessage('Typical weight not valid')
        else:
            typical_weight = None # Covers the empty string case

        main_ingredients = [ingredient.strip() for ingredient in main_ingredients.split(',')]

        if not main_ingredients or not main_ingredients[0]:
            raise ErrorMessage('Main ingredients are required')

        Food.objects.create(created_by = request.user,
                            name = name,
                            main_ingredients = main_ingredients,
                            typical_weight = typical_weight)

        data['added_name'] = name

    return render(request, 'food_add.html', {'data': data})

@private_view
def food_observations(request):

    data = {}

    # Get back the food if any
    food_uuid = request.GET.get('food_uuid', None)
    if food_uuid:
        food = Food.objects.get(uuid=food_uuid)
        data['food'] = food

    # Get the observation
    if food_uuid:
        observations = FoodObservation.objects.filter(food=food)
    else:
        observations = FoodObservation.objects.all()
    data['observations'] = observations

    return render(request, 'food_observations.html', {'data': data})

@private_view
def food_observations_add(request):

    def parse_int_field(value, field_name):
        if not value:
            return None
        else:
            try:
                return int(value)
            except:
                raise ErrorMessage('"{}" value not valid for "{}"'.format(value, field_name))

    data = {}
    if request.method == 'POST':

        # Get back the food
        food_uuid = request.POST.get('food_uuid', None)
        food = Food.objects.get(uuid=food_uuid)
        data['food'] = food

        # Nutritional facts
        cho = parse_int_field(value=request.POST.get('cho', None), field_name='cho')
        proteins = parse_int_field(value=request.POST.get('proteins', None), field_name='proteins')
        fibers = parse_int_field(value=request.POST.get('fibers', None), field_name='fibers')
        fat = parse_int_field(value=request.POST.get('fat', None), field_name='fat')

        if cho is None and proteins is None and fibers is None and fat is None:
            raise ErrorMessage('Empty observation')

        FoodObservation.objects.create(created_by = request.user,
                                       food = food,
                                       cho_ratio = cho/100,
                                       protein_ratio = proteins/100,
                                       fiber_ratio = fibers/100,
                                       fat_ratio = fat/100)
        data['added'] = True

    else:
        # Get back the food
        food_uuid = request.GET.get('food_uuid', None)
        data['food'] = Food.objects.get(uuid=food_uuid)

    return render(request, 'food_observations_add.html', {'data': data})

@public_view
def chat(request):

    data = {}
    if request.method == 'POST':

        # Get back the food
        message = request.POST.get('message', None)
        if not message:
            raise ErrorMessage('Got no message at all')
        data['message'] = message

        # Filter foods
        foods = Food.objects.filter(name__icontains=message)
        if not foods:
            data['reply']  = 'Non ho trovato nessun alimento specifico corrispondente a "{}". Puoi provare ad essere più generale?'.format(message)
            return render(request, 'chat.html', {'data': data})

        # Process all observations for matching foods
        cho_observations = []
        protein_observations = []
        fiber_observations = []
        fat_observations = []
        for food in foods:
            for observation in food.observations.all():
                if observation.cho is not None:
                    cho_observations.append(observation.cho)
                if observation.proteins is not None:
                    protein_observations.append(observation.proteins)
                if observation.fibers is not None:
                    fiber_observations.append(observation.fibers)
                if observation.fat is not None:
                    fat_observations.append(observation.fat)

        if not cho_observations and not protein_observations and not fiber_observations and not fat_observations:
            data['reply']  = 'Non ho trovato nessun alimento specifico corrispondente a "{}". Puoi provare ad essere più generale?'.format(message)
            return render(request, 'chat.html', {'data': data})

        # Compute averages
        if cho_observations:
            cho = sum(cho_observations) / len(cho_observations)
        if protein_observations:
            proteins = sum(protein_observations) / len(protein_observations)
        if fiber_observations:
            fibers = sum(fiber_observations) / len(fiber_observations)
        if fat_observations:
            fat = sum(fat_observations) / len(fat_observations)

        # Compose reply
        matching_foods_string = ''
        for food in foods:
            matching_foods_string += '{}, '.format(food.name)
        matching_foods_string = matching_foods_string[0:-2]
        reply =  'Per "{}" ho trovato "{}". Valori nutrizionali medi: '.format(message, matching_foods_string)
        if cho_observations:
            reply += '{}g di carboidrati, '.format(cho)
        if protein_observations:
            reply += '{}g di proteine, '.format(proteins)
        if fiber_observations:
            reply += '{}g di fibre e '.format(fibers)
        if fat_observations:
            reply += '{}g di grassi '.format(fat)
        reply += 'per 100g. '

        # Set the reply in the data
        data['reply'] = reply

    return render(request, 'chat.html', {'data': data})

