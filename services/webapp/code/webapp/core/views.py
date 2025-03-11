from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotFound
from django.contrib.auth.models import User
from django.shortcuts import redirect
from .models import Food, FoodObservation
from .decorators import public_view, private_view
from .exceptions import ErrorMessage
from .bot import Bot
import uuid

# Setup logging
import logging
logger = logging.getLogger(__name__)

conversations_cache = {}

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
        small_serving = request.POST.get('small_serving', None)
        medium_serving = request.POST.get('medium_serving', None)
        large_serving = request.POST.get('large_serving', None)

        if not name:
            raise ErrorMessage('Food name is required')

        if not main:
            raise ErrorMessage('Food name is required')

        def make_int(parameter, name):
            if parameter:
                try:
                    parameter = int(parameter)
                except:
                    raise ErrorMessage('Value for "{}" is not valid'.format(name))
            else:
                parameter = None # Covers the empty string case
            return parameter

        # Make parameters int
        small_serving = make_int(small_serving, 'small_serving')
        medium_serving = make_int(medium_serving, 'medium_serving')
        large_serving = make_int(large_serving, 'large_serving')

        main_ingredients = [ingredient.strip() for ingredient in main_ingredients.split(',')]

        if not main_ingredients or not main_ingredients[0]:
            raise ErrorMessage('Main ingredients are required')

        Food.objects.create(created_by = request.user,
                            name = name,
                            main_ingredients = main_ingredients,
                            small_serving = small_serving,
                            medium_serving = medium_serving,
                            large_serving = large_serving)

        data['added_name'] = name

    return render(request, 'food_add.html', {'data': data})

@private_view
def food_load(request):
    data = {}
    if request.method == 'POST':

        errors = {}

        # Get file if any
        fileinput = request.FILES.get('fileinput', None)
        logger.info('Loaded fileinput="{}"'.format(fileinput))

        if not fileinput:
            raise ErrorMessage('No file provided?')

        # Load file content
        fild_uuid = str(uuid.uuid4())
        file_content = None
        if fileinput:
            with open('/tmp/{}'.format(fild_uuid), 'wb+') as destination:
                for chunk in fileinput.chunks():
                    destination.write(chunk)
            for chunk in fileinput.chunks():
                if not file_content:
                    file_content = chunk
                else:
                    file_content += chunk
        #logger.debug(file_content)

        import csv
        with open('/tmp/{}'.format(fild_uuid), mode='r') as f:
            reader = csv.DictReader(f)
            csv_data = [row for row in reader]

        for food in Food.objects.all():
            food.delete()

        for i, entry in enumerate(csv_data):
            if not entry['Nome descrittivo']:
                continue
            else:
                name = entry['Nome descrittivo'].strip()
            if not entry['Ingredienti principali']:
                errors[i+2] = 'Nessun ingrediente principale per "{}"?'.format(name)
                continue
            else:
                main_ingredients = [ingredient.strip() for ingredient in entry['Ingredienti principali'].split(',')]

            small_serving = None
            medium_serving = None
            large_serving = None

            small_piece = None
            medium_piece = None
            large_piece = None

            cho_content = None
            protein_content = None
            fiber_content = None
            fat_content = None

            liquid = False

            for key in entry.keys():

                # Servings
                if 'porzione' in key.lower():
                    if 'piccola' in key.lower():
                        if entry[key].strip():
                            small_serving = int(float(entry[key]))
                    if 'media' in key.lower():
                        if entry[key].strip():
                            medium_serving = int(float(entry[key]))
                    if 'grande' in key.lower():
                        if entry[key].strip():
                            large_serving = int(float(entry[key]))

                # Pieces
                if 'pezzo' in key.lower():
                    if 'piccolo' in key.lower():
                        if entry[key].strip():
                            small_piece = int(float(entry[key]))
                    if 'medio' in key.lower():
                        if entry[key].strip():
                            medium_piece = int(float(entry[key]))
                    if 'grande' in key.lower():
                        if entry[key].strip():
                            large_piece = int(float(entry[key]))

                # Values
                if 'cho' in key.lower():
                    if entry[key].strip():
                        cho_content = float(entry[key])
                if 'protein' in key.lower():
                    if entry[key].strip():
                        protein_content = float(entry[key])
                if 'fibre' in key.lower():
                    if entry[key].strip():
                        fiber_content = float(entry[key])
                if 'proteine' in key.lower():
                    if entry[key].strip():
                        fat_content = float(entry[key])

                # Liquid
                if 'tipo' in key.lower():
                    if entry[key].strip() == 'bevanda':
                        liquid = True

            if not cho_content and not protein_content and not fiber_content and not fat_content:
                errors[i+2] = 'Nessun valore nutrizionale per "{}"?'.format(name)
                continue

            food = Food.objects.create(created_by = request.user,
                                       name = name,
                                       main_ingredients = main_ingredients,
                                       small_serving = small_serving,
                                       medium_serving = medium_serving,
                                       large_serving = large_serving,
                                       small_piece = small_piece,
                                       medium_piece = medium_piece,
                                       large_piece = large_piece,
                                       liquid = liquid)

            FoodObservation.objects.create(created_by = request.user,
                                           food = food,
                                           cho_ratio = cho_content/100 if cho_content is not None else None,
                                           protein_ratio = protein_content/100 if protein_content  is not None else None,
                                           fiber_ratio = fiber_content/100 if fiber_content  is not None else None,
                                           fat_ratio = fat_content/100 if fat_content is not None else None)
        data['errors'] = errors
        data['loaded'] = True
        logger.info('Deleted all content and loaded database')

    return render(request, 'food_load.html', {'data': data})

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
                                       cho_ratio = cho/100 if cho else None,
                                       protein_ratio = proteins/100 if proteins else None,
                                       fiber_ratio = fibers/100 if fibers else None,
                                       fat_ratio = fat/100 if fat else None)
        data['added'] = True

    else:
        # Get back the food
        food_uuid = request.GET.get('food_uuid', None)
        data['food'] = Food.objects.get(uuid=food_uuid)

    return render(request, 'food_observations_add.html', {'data': data})

@csrf_exempt
@public_view
def chat(request):

    data = {}

    if request.method == 'POST':

        # Get the conversation id
        conversation_id = request.POST.get('conversation_id', None)

        # Load previous messages
        if conversation_id not in conversations_cache:
            conversations_cache[conversation_id] = []

        # Get the message
        message = request.POST.get('message', None)
        if not message:
            raise ErrorMessage('Got no message at all')

        # Ask the bot to answer
        bot = Bot()
        reply = bot.answer(message)

        # Safety measure to prevent HTML tags injection
        reply = reply.replace('<', '').replace('>','')

        # Render newline in HTML
        reply = reply.replace('\n', '<br/>')

        # Render bold  in HTML
        reply = reply.replace('/*', '</b>').replace('*','<b>')


        # Add the original message and the reply in the conversation data data
        conversations_cache[conversation_id].append({'message':message, 'reply':reply})

        # And set the conversation in the page data
        data['conversation'] = conversations_cache[conversation_id]

    else:
        conversation_id = str(uuid.uuid4())

    # Set the conversation id in the page
    data['conversation_id'] = conversation_id

    return render(request, 'chat.html', {'data': data})

