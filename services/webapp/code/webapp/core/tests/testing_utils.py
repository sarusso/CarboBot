import time
import requests
from django.contrib.auth.models import User

def get_or_create_user(username='testuser', password='testpass'):
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        user = User.objects.create_user(username=username, password=password)
    return user

def reset_test_indexes():
    # Reset test search indexes
    for index_name in ['test_food', 'test_food_servings', 'test_food_pieces']:
        url = 'http://search/api/v1/manage/'
        payload = {
            'command': 'reset',
            'index_name': index_name,
            'confirmation_code': 'DEADBEEF'
        }
        response = requests.post(url, json=payload)
        if not response.status_code == 200:
            raise Exception('Cannot reset the search service test index. Is it running? ({})'.format(response.content))
        if not 'Reset successfully executed' in str(response.content):
            raise Exception('Cannot reset the search service test index. Is it running? ({})'.format(response.content))

def delete_test_indexes():
    # Delete test search indexes
    for index_name in ['test_food', 'test_food_servings', 'test_food_pieces']:
        url = 'http://search/api/v1/manage/'
        payload = {
            'command': 'delete',
            'index_name': index_name,
            'confirmation_code': 'DEADBEEF'
        }
        requests.post(url, json=payload)

def add_to_test_index(data):
    if not isinstance(data, list):
        data = [data]
    for item in data:
        # Add to the test search index
        url = 'http://search/api/v1/add/'
        item['index_name'] = 'test_food'
        response = requests.post(url, json=item)
    time.sleep(1) # TODO: meh...
    return response

