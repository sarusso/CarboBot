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

def add_to_test_index(data):
    if not isinstance(data, list):
        data = [data]
    for item in data:
        # Add to the test search index
        url = 'http://search/api/v1/add/'
        item['index_name'] = 'food_index_test'
        response = requests.post(url, json=item)
    time.sleep(1) # TODO: meh...
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

        # Add something
        item = { "uuid": "00000000-0000-0000-0000-000000000001", "description": "Insalata caprese", "ingredients": ["mozzarella", "pomodoro", "basilico"] }
        add_to_test_index(item)

        # Get it back searching for "caprese"
        url = 'http://search/api/v1/search?q=caprese&index_name=food_index_test&min_score=0&max_diff=1'
        response = requests.get(url)
        self.assertEqual(response.status_code,200)
        expected = [{'_index': 'food_index_test', '_type': '_doc', '_id': '00000000-0000-0000-0000-000000000001', '_score': 0.2876821, '_relative_score': 1.0, '_source': {'uuid': '00000000-0000-0000-0000-000000000001', 'description': 'Insalata caprese', 'ingredients': ['mozzarella', 'pomodoro', 'basilico'], 'index_name': 'food_index_test'}}]
        self.assertEqual(response.json(), expected)

        # Test for boundaries
        url = 'http://search/api/v1/search?q=caprese&index_name=food_index_test&min_score=0.3&max_diff=1'
        response = requests.get(url)
        self.assertEqual(response.status_code,200)
        self.assertEqual(len(response.json()), 0)

        url = 'http://search/api/v1/search?q=caprese&index_name=food_index_test&min_score=0&max_diff=0'
        response = requests.get(url)
        self.assertEqual(response.status_code,200)
        self.assertEqual(len(response.json()), 1)

        # Add something more
        item2 = { "uuid": "00000000-0000-0000-0000-000000000002", "description": "Insalata di riso con verdure", "ingredients": ["riso", "carote", "piselli"] }
        item3 = { "uuid": "00000000-0000-0000-0000-000000000003", "description": "Insalata di riso con pollo", "ingredients": ["riso", "pollo", "maionese"] }
        item4 = { "uuid": "00000000-0000-0000-0000-000000000004", "description": "Insalata di riso con sottaceti vari", "ingredients": ["riso", "sottaceti", "olio"] }
        add_to_test_index([item2,item3,item4])

        # Search for "insalata" will get only the first ("mozzarella" main ingredient)
        url = 'http://search/api/v1/search?q=insalata&index_name=food_index_test&min_score=0&max_diff=1'
        response = requests.get(url)
        self.assertEqual(response.status_code,200)
        self.assertEqual(len(response.json()),1)

        # Search for "insalata di riso" will get the first two "insalata di riso", with max_diff=0 (same match)
        url = 'http://search/api/v1/search?q=insalata%20di%20riso&index_name=food_index_test&min_score=0&max_diff=0'
        response = requests.get(url)
        self.assertEqual(response.status_code,200)
        response_json = response.json()
        self.assertEqual(len(response_json),2)
        uuids = [hit['_id'] for hit in response_json]
        self.assertTrue('00000000-0000-0000-0000-000000000002' in uuids)
        self.assertTrue('00000000-0000-0000-0000-000000000003' in uuids)

        # Search for "insalata di riso" will get the first two "insalata di riso", with max_diff=0.1 (very close matches)
        url = 'http://search/api/v1/search?q=insalata%20di%20riso&index_name=food_index_test&min_score=0&max_diff=0.05'
        response = requests.get(url)
        self.assertEqual(response.status_code,200)
        response_json = response.json()
        self.assertEqual(len(response_json),2)
        uuids = [hit['_id'] for hit in response_json]
        self.assertTrue('00000000-0000-0000-0000-000000000002' in uuids)
        self.assertTrue('00000000-0000-0000-0000-000000000003' in uuids)
        self.assertEqual(response_json[0]['_relative_score'], 1)
        self.assertEqual(response_json[1]['_relative_score'], 1)

        # Search for "insalata di riso" will get all the "insalata di riso", with max_diff=0.3 (close matches)
        url = 'http://search/api/v1/search?q=insalata%20di%20riso&index_name=food_index_test&min_score=0&max_diff=0.2'
        response = requests.get(url)
        self.assertEqual(response.status_code,200)
        response_json = response.json()
        self.assertEqual(len(response_json),3)
        uuids = [hit['_id'] for hit in response_json]
        self.assertTrue('00000000-0000-0000-0000-000000000002' in uuids)
        self.assertTrue('00000000-0000-0000-0000-000000000003' in uuids)
        self.assertTrue('00000000-0000-0000-0000-000000000004' in uuids)
        self.assertEqual(response_json[0]['_relative_score'], 1)
        self.assertEqual(response_json[1]['_relative_score'], 1)
        self.assertAlmostEqual(response_json[2]['_relative_score'], 0.9200, places=3)

        # Add somehting different now but with same main ingredient
        item5 = { "uuid": "00000000-0000-0000-0000-000000000038", "description": "Arancini di riso", "ingredients": ["riso", "carne", "piselli"] }
        add_to_test_index(item5)

        # Search for "insalata di riso" mjust still get only all the three "instalata di riso", score of the third slightly changes now
        url = 'http://search/api/v1/search?q=insalata%20di%20riso&index_name=food_index_test&min_score=0&max_diff=0.2'
        response = requests.get(url)
        self.assertEqual(response.status_code,200)
        response_json = response.json()
        self.assertEqual(len(response_json),3)
        uuids = [hit['_id'] for hit in response_json]
        self.assertTrue('00000000-0000-0000-0000-000000000002' in uuids)
        self.assertTrue('00000000-0000-0000-0000-000000000003' in uuids)
        self.assertTrue('00000000-0000-0000-0000-000000000004' in uuids)
        self.assertEqual(response_json[0]['_relative_score'], 1)
        self.assertEqual(response_json[1]['_relative_score'], 1)
        self.assertAlmostEqual(response_json[2]['_relative_score'], 0.9171, places=3)

        # Search for "arancina" (sorry, Catania)
        url = 'http://search/api/v1/search?q=arancina&index_name=food_index_test&min_score=0&max_diff=0.2'
        response = requests.get(url)
        self.assertEqual(response.status_code,200)
        response_json = response.json()
        self.assertEqual(len(response_json),1)
        self.assertEqual(response_json[0]['_id'], '00000000-0000-0000-0000-000000000038')

        # Search for "riso". Arancini come first as the description is shorter
        url = 'http://search/api/v1/search?q=riso&index_name=food_index_test&min_score=0&max_diff=1'
        response = requests.get(url)
        self.assertEqual(response.status_code,200)
        response_json = response.json()
        self.assertEqual(response_json[0]['_id'],'00000000-0000-0000-0000-000000000038')
        self.assertAlmostEqual(response_json[0]['_score'], 0.32575765, places=3)
        self.assertEqual(response_json[1]['_id'],'00000000-0000-0000-0000-000000000002')
        self.assertAlmostEqual(response_json[1]['_score'], 0.26688576, places=3)
        self.assertEqual(response_json[2]['_id'],'00000000-0000-0000-0000-000000000003')
        self.assertAlmostEqual(response_json[2]['_score'], 0.26688576, places=3)
        self.assertEqual(response_json[3]['_id'],'00000000-0000-0000-0000-000000000004')
        self.assertAlmostEqual(response_json[3]['_score'], 0.24476814, places=3)

        # ..and for "eiso" (a typo), which lowers the score
        url = 'http://search/api/v1/search?q=fiso&index_name=food_index_test&min_score=0&max_diff=1'
        response = requests.get(url)
        self.assertEqual(response.status_code,200)
        response_json = response.json()
        self.assertEqual(response_json[0]['_id'],'00000000-0000-0000-0000-000000000038')
        self.assertAlmostEqual(response_json[0]['_score'], 0.24431825, places=3)
        self.assertEqual(response_json[1]['_id'],'00000000-0000-0000-0000-000000000002')
        self.assertAlmostEqual(response_json[1]['_score'], 0.20016432, places=3)
        self.assertEqual(response_json[2]['_id'],'00000000-0000-0000-0000-000000000003')
        self.assertAlmostEqual(response_json[2]['_score'], 0.20016432, places=3)
        self.assertEqual(response_json[3]['_id'],'00000000-0000-0000-0000-000000000004')
        self.assertAlmostEqual(response_json[3]['_score'], 0.18357614, places=3)

        # Lastly, search for nonsense: no results at all
        url = 'http://search/api/v1/search?q=girasole&index_name=food_index_test&min_score=0&max_diff=1'
        response = requests.get(url)
        self.assertEqual(response.status_code,200)
        self.assertEqual(len(response.json()),0)

