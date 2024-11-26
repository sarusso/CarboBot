import requests
from django.test import TestCase
from ..models import Food
from django.contrib.auth.models import User
import time

# Note: these are end-to-end tests, using two other services in chain (search and elastic)

def reset_test_index():
    # Reset test search index
    url = 'http://search/api/v1/manage/'
    payload = {
        'command': 'reset',
        'index_name': 'food_index_test',
        'confirmation_code': 'DEADBEEF'
    }
    response = requests.post(url, json=payload)
    if not response.status_code == 200:
        raise Exception('Cannot reset the search service test index. Is it running? ({})'.format(response.content))
    if not 'Reset successfully executed' in str(response.content):
        raise Exception('Cannot reset the search service test index. Is it running? ({})'.format(response.content))

def delete_test_index():
    # Delete test search index
    url = 'http://search/api/v1/manage/'
    payload = {
        'command': 'delete',
        'index_name': 'food_index_test',
        'confirmation_code': 'DEADBEEF'
    }
    requests.post(url, json=payload)

def add_to_test_index(item):
    # Add to the test search index
    url = 'http://search/api/v1/add/'
    item['index_name'] = 'food_index_test'
    response = requests.post(url, json=item)
    time.sleep(3) # TODO: meh...
    return response


class TestBaseOperations(TestCase):

    # @classmethod
    # def setUpClass(cls):
    #     super().setUpClass()
    #
    # @classmethod
    # def tearDownClass(cls):
    #     delete_test_index()
    #     super().tearDownClass()

    def setUp(self):
        reset_test_index()
        self.test_user = User.objects.create_user(username='testuser', password='testpassword')
        super().setUp()

    def tearDown(self):
        delete_test_index()

    def test_search_service(self):

        # Nothing there
        url = 'http://search/api/v1/search?q=insalata&index_name=food_index_test&min_score=0&max_diff=1'
        response = requests.get(url)
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json(), [])

        # Insert something now
        item = { "uuid": "00000000-0000-0000-0000-000000000001", "description": "Insalata caprese con mozzarella di bufala", "ingredients": ["mozzarella", "pomodoro", "basilico"] }
        add_to_test_index(item)

        # Get it back
        url = 'http://search/api/v1/search?q=caprese&index_name=food_index_test&min_score=0&max_diff=1'
        response = requests.get(url)
        self.assertEqual(response.status_code,200)
        expected = [{'_index': 'food_index_test', '_type': '_doc', '_id': '00000000-0000-0000-0000-000000000001', '_score': 0.2876821, '_relative_score': 1.0, '_source': {'uuid': '00000000-0000-0000-0000-000000000001', 'description': 'Insalata caprese con mozzarella di bufala', 'ingredients': ['mozzarella', 'pomodoro', 'basilico'], 'index_name': 'food_index_test'}}]
        self.assertEqual(response.json(), expected)

        # Test for boundaries
        url = 'http://search/api/v1/search?q=caprese&index_name=food_index_test&min_score=0.3&max_diff=1'
        response = requests.get(url)
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json(), [])

        url = 'http://search/api/v1/search?q=caprese&index_name=food_index_test&min_score=0&max_diff=0'
        response = requests.get(url)
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json(), [])

        # Add something more
        item2 = { "uuid": "00000000-0000-0000-0000-000000000002", "description": "Insalata di riso con verdure", "ingredients": ["riso", "carote", "piselli"] }
        add_to_test_index(item2)

        # Search now, get them both
        url = 'http://search/api/v1/search?q=inslaata&index_name=food_index_test&min_score=0&max_diff=1'
        response = requests.get(url)
        self.assertEqual(response.status_code,200)
        self.assertEqual(len(response.json()),2)

