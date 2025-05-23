import requests
from django.test import TestCase
from ..models import Food
from ..utils import SearchService, message_parser
from django.contrib.auth.models import User
import time

# Note: these are end-to-end tests, using two other services in chain (search and elastic)

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


class TestSearchService(TestCase):

    # @classmethod
    # def setUpClass(cls):
    #     super().setUpClass()
    #
    # @classmethod
    # def tearDownClass(cls):
    #     delete_test_index()
    #     super().tearDownClass()

    def setUp(self):
        reset_test_indexes()
        self.test_user = User.objects.create_user(username='testuser', password='testpassword')
        super().setUp()

    def tearDown(self):
        delete_test_indexes()

    def test_search_service_api_basic(self):

        # Nothing there
        url = 'http://search/api/v1/search?q=insalata&index_name=test_food&min_score=0&max_diff=1'
        response = requests.get(url)
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json(), [])

        # Add something
        item = { "uuid": "00000000-0000-0000-0000-000000000001", "description": "Insalata caprese", "ingredients": ["mozzarella", "pomodoro", "basilico"] }
        add_to_test_index(item)

        # Get it back searching for "caprese"
        url = 'http://search/api/v1/search?q=caprese&index_name=test_food&min_score=0&max_diff=1'
        response = requests.get(url)
        self.assertEqual(response.status_code,200)
        expected = [{'_index': 'test_food', '_type': '_doc', '_id': '00000000-0000-0000-0000-000000000001', '_score': 0.2876821, '_relative_score': 1.0, '_source': {'uuid': '00000000-0000-0000-0000-000000000001', 'description': 'Insalata caprese', 'ingredients': ['mozzarella', 'pomodoro', 'basilico'], 'index_name': 'test_food'}}]
        self.assertEqual(response.json(), expected)

        # Test for boundaries
        url = 'http://search/api/v1/search?q=caprese&index_name=test_food&min_score=0.3&max_diff=1'
        response = requests.get(url)
        self.assertEqual(response.status_code,200)
        self.assertEqual(len(response.json()), 0)

        url = 'http://search/api/v1/search?q=caprese&index_name=test_food&min_score=0&max_diff=0'
        response = requests.get(url)
        self.assertEqual(response.status_code,200)
        self.assertEqual(len(response.json()), 1)

        # Add something more
        item2 = { "uuid": "00000000-0000-0000-0000-000000000002", "description": "Insalata di riso con verdure", "ingredients": ["riso", "carote", "piselli"] }
        item3 = { "uuid": "00000000-0000-0000-0000-000000000003", "description": "Insalata di riso con pollo", "ingredients": ["riso", "pollo", "maionese"] }
        item4 = { "uuid": "00000000-0000-0000-0000-000000000004", "description": "Insalata di riso con sottaceti vari", "ingredients": ["riso", "sottaceti", "olio"] }
        add_to_test_index([item2,item3,item4])

        # Search for "insalata" will get only the first ("mozzarella" main ingredient)
        url = 'http://search/api/v1/search?q=insalata&index_name=test_food&min_score=0&max_diff=1'
        response = requests.get(url)
        self.assertEqual(response.status_code,200)
        self.assertEqual(len(response.json()),1)

        # Search for "insalata di riso" will get the first two "insalata di riso", with max_diff=0 (same match)
        url = 'http://search/api/v1/search?q=insalata%20di%20riso&index_name=test_food&min_score=0&max_diff=0'
        response = requests.get(url)
        self.assertEqual(response.status_code,200)
        response_json = response.json()
        self.assertEqual(len(response_json),2)
        uuids = [hit['_id'] for hit in response_json]
        self.assertTrue('00000000-0000-0000-0000-000000000002' in uuids)
        self.assertTrue('00000000-0000-0000-0000-000000000003' in uuids)

        # Search for "insalata di riso" will get the first two "insalata di riso", with max_diff=0.1 (very close matches)
        url = 'http://search/api/v1/search?q=insalata%20di%20riso&index_name=test_food&min_score=0&max_diff=0.05'
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
        url = 'http://search/api/v1/search?q=insalata%20di%20riso&index_name=test_food&min_score=0&max_diff=0.2'
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
        url = 'http://search/api/v1/search?q=insalata%20di%20riso&index_name=test_food&min_score=0&max_diff=0.2'
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
        url = 'http://search/api/v1/search?q=arancina&index_name=test_food&min_score=0&max_diff=0.2'
        response = requests.get(url)
        self.assertEqual(response.status_code,200)
        response_json = response.json()
        self.assertEqual(len(response_json),1)
        self.assertEqual(response_json[0]['_id'], '00000000-0000-0000-0000-000000000038')

        # Search for "riso". Arancini come first as the description is shorter
        url = 'http://search/api/v1/search?q=riso&index_name=test_food&min_score=0&max_diff=1'
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
        url = 'http://search/api/v1/search?q=fiso&index_name=test_food&min_score=0&max_diff=1'
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
        url = 'http://search/api/v1/search?q=girasole&index_name=test_food&min_score=0&max_diff=1'
        response = requests.get(url)
        self.assertEqual(response.status_code,200)
        self.assertEqual(len(response.json()),0)


    def test_search_service_class_with_food_model(self):

        search_service = SearchService(index_prefix='test_')

        food1 = Food(uuid='00000000-0000-0000-0000-000000000100',
                     name='My Food',
                     main_ingredients = ['Ingredient 1', 'Ingredient 2', 'Ingredient 3'],
                     created_by=self.test_user )
        food1.save(search_service=search_service)
        food2 = Food(uuid='00000000-0000-0000-0000-000000000101',
                     name='My Other Food',
                     main_ingredients = ['Ingredient 1', 'Ingredient 2', 'Ingredient 3'],
                     created_by=self.test_user )
        food2.save(search_service=search_service)
        time.sleep(1)

        # Can we search them back with the search service?
        hits = search_service.query('Food')
        self.assertEqual(len(hits),2)
        self.assertEqual(hits[0]['_id'],'00000000-0000-0000-0000-000000000100')
        self.assertEqual(hits[1]['_id'],'00000000-0000-0000-0000-000000000101')

        # Ok, now test the built-in Food query
        results = Food.query('Food', search_service=search_service)
        self.assertEqual(len(results),2)
        self.assertEqual(results[0].uuid,food1.uuid)
        self.assertEqual(results[1].uuid,food2.uuid)

        # Check another save is not possible
        food1.name = 'Changed name'
        with self.assertRaises(Exception):
            food1.save()

        # Check the delete
        food1.delete(search_service=search_service)
        time.sleep(1)
        results = Food.query('Food', search_service=search_service)
        self.assertEqual(len(results),1)
        self.assertEqual(results[0].uuid,food2.uuid)


    def test_search_service_class_with_food_model_and_variants(self):

        search_service = SearchService(index_prefix='test_')

        food1 = Food(uuid='00000000-0000-0000-0000-000000000100',
                     name='My Food',
                     main_ingredients = ['Ingredient 1', 'Ingredient 2', 'Ingredient 3'],
                     created_by=self.test_user,
                     small_serving=10)
        food1.save(search_service=search_service)
        food2 = Food(uuid='00000000-0000-0000-0000-000000000101',
                     name='My Other Food',
                     main_ingredients = ['Ingredient 1', 'Ingredient 2', 'Ingredient 3'],
                     created_by=self.test_user)
        food2.save(search_service=search_service)
        time.sleep(1)

        # Can we search the serving variant back with the search service?
        hits = search_service.query('Food', variant='servings')
        self.assertEqual(len(hits),1)
        self.assertEqual(hits[0]['_id'],'00000000-0000-0000-0000-000000000100')

        # Ok, now test the built-in Food query
        results = Food.query('Food', search_service=search_service, variant='servings')
        self.assertEqual(len(results),1)
        self.assertEqual(results[0].uuid,food1.uuid)

        # Check the delete that has to remove on both indexes
        food1.delete(search_service=search_service)
        time.sleep(1)
        results = Food.query('Food', search_service=search_service)
        self.assertEqual(len(results),1) # Only "My Other Food" left
        self.assertEqual(results[0].uuid,food2.uuid)
        hits = search_service.query('Food', variant='servings')
        self.assertEqual(len(hits),0)

class TestMessageParser(TestCase):

    def test_message_parser_basic(self):

        parsed = message_parser('pasta al pomodoro')
        self.assertEqual(parsed['food'], 'pasta al pomodoro')
        self.assertEqual(parsed['amount'], None)
        self.assertEqual(parsed['pieces'], None)
        self.assertEqual(parsed['size'], None)
        self.assertEqual(parsed['details'], False)

        parsed = message_parser('80g pasta al pomodoro')
        self.assertEqual(parsed['food'], 'pasta al pomodoro')
        self.assertEqual(parsed['amount'], 80)
        self.assertEqual(parsed['pieces'], None)
        self.assertEqual(parsed['size'], None)
        self.assertEqual(parsed['details'], False)

        parsed = message_parser('80 pasta al pomodoro')
        self.assertEqual(parsed['food'], 'pasta al pomodoro')
        self.assertEqual(parsed['amount'], None)
        self.assertEqual(parsed['pieces'], 80)
        self.assertEqual(parsed['size'], None)
        self.assertEqual(parsed['details'], False)

        parsed = message_parser('80 g pasta al pomodoro')
        self.assertEqual(parsed['food'], 'pasta al pomodoro')
        self.assertEqual(parsed['amount'], 80)
        self.assertEqual(parsed['pieces'], None)
        self.assertEqual(parsed['size'], None)
        self.assertEqual(parsed['details'], False)

        parsed = message_parser('80 g pasta al pomodoro dettagli')
        self.assertEqual(parsed['food'], 'pasta al pomodoro')
        self.assertEqual(parsed['amount'], 80)
        self.assertEqual(parsed['pieces'], None)
        self.assertEqual(parsed['size'], None)
        self.assertEqual(parsed['details'], True)

        parsed = message_parser('80 g pasta al pomodoro con dettagli')
        self.assertEqual(parsed['food'], 'pasta al pomodoro')
        self.assertEqual(parsed['amount'], 80)
        self.assertEqual(parsed['pieces'], None)
        self.assertEqual(parsed['size'], None)
        self.assertEqual(parsed['details'], True)

        parsed = message_parser('piccola brioche')
        self.assertEqual(parsed['food'], 'brioche')
        self.assertEqual(parsed['amount'], None)
        self.assertEqual(parsed['pieces'], None)
        self.assertEqual(parsed['size'], 's')
        self.assertEqual(parsed['details'], False)

        parsed = message_parser('poca pasta')
        self.assertEqual(parsed['food'], 'pasta')
        self.assertEqual(parsed['amount'], None)
        self.assertEqual(parsed['pieces'], None)
        self.assertEqual(parsed['size'], 's')
        self.assertEqual(parsed['details'], False)

        parsed = message_parser('grande pizza')
        self.assertEqual(parsed['food'], 'pizza')
        self.assertEqual(parsed['amount'], None)
        self.assertEqual(parsed['pieces'], None)
        self.assertEqual(parsed['size'], 'l')
        self.assertEqual(parsed['details'], False)

        parsed = message_parser('pizza grande')
        self.assertEqual(parsed['food'], 'pizza')
        self.assertEqual(parsed['amount'], None)
        self.assertEqual(parsed['pieces'], None)
        self.assertEqual(parsed['size'], 'l')
        self.assertEqual(parsed['details'], False)

        # With pieces
        parsed = message_parser('un pomodoro')
        self.assertEqual(parsed['food'], 'pomodoro')
        self.assertEqual(parsed['amount'], None)
        self.assertEqual(parsed['pieces'], 1)
        self.assertEqual(parsed['size'], None)
        self.assertEqual(parsed['details'], False)

        parsed = message_parser('un\' arancia')
        self.assertEqual(parsed['food'], 'arancia')
        self.assertEqual(parsed['amount'], None)
        self.assertEqual(parsed['pieces'], 1)
        self.assertEqual(parsed['size'], None)
        self.assertEqual(parsed['details'], False)

        parsed = message_parser('due arance')
        self.assertEqual(parsed['food'], 'arance')
        self.assertEqual(parsed['amount'], None)
        self.assertEqual(parsed['pieces'], 2)
        self.assertEqual(parsed['size'], None)
        self.assertEqual(parsed['details'], False)


    def test_message_parser_servings_and_pieces(self):

        # Crackers
        parsed = message_parser('cracker')
        self.assertEqual(parsed['food'], 'cracker')
        self.assertEqual(parsed['amount'], None)
        self.assertEqual(parsed['pieces'], None)
        self.assertEqual(parsed['size'], None)
        self.assertEqual(parsed['details'], False)
        self.assertEqual(parsed['serving'], None)

        parsed = message_parser('un cracker')
        self.assertEqual(parsed['food'], 'cracker')
        self.assertEqual(parsed['amount'], None)
        self.assertEqual(parsed['pieces'], 1)
        self.assertEqual(parsed['size'], None)
        self.assertEqual(parsed['details'], False)
        self.assertEqual(parsed['serving'], None)

        parsed = message_parser('un cracker piccolo')
        self.assertEqual(parsed['food'], 'cracker')
        self.assertEqual(parsed['amount'], None)
        self.assertEqual(parsed['pieces'], 1)
        self.assertEqual(parsed['size'], 's')
        self.assertEqual(parsed['details'], False)
        self.assertEqual(parsed['serving'], None)

        parsed = message_parser('una porzione di cracker')
        self.assertEqual(parsed['food'], 'cracker')
        self.assertEqual(parsed['amount'], None)
        self.assertEqual(parsed['pieces'], None)
        self.assertEqual(parsed['size'], None)
        self.assertEqual(parsed['details'], False)
        self.assertEqual(parsed['serving'], 1)

        parsed = message_parser('una confezione di cracker')
        self.assertEqual(parsed['food'], 'cracker')
        self.assertEqual(parsed['amount'], None)
        self.assertEqual(parsed['pieces'], None)
        self.assertEqual(parsed['size'], None)
        self.assertEqual(parsed['details'], False)
        self.assertEqual(parsed['serving'], 1)

        parsed = message_parser('un pacchetto di cracker')
        self.assertEqual(parsed['food'], 'cracker')
        self.assertEqual(parsed['amount'], None)
        self.assertEqual(parsed['pieces'], None)
        self.assertEqual(parsed['size'], None)
        self.assertEqual(parsed['details'], False)
        self.assertEqual(parsed['serving'], 1)

        parsed = message_parser('un pacchetto di cracker piccolo')
        self.assertEqual(parsed['food'], 'cracker')
        self.assertEqual(parsed['amount'], None)
        self.assertEqual(parsed['pieces'], None)
        self.assertEqual(parsed['size'], 's')
        self.assertEqual(parsed['details'], False)
        self.assertEqual(parsed['serving'], 1)

        parsed = message_parser('40g cracker')
        self.assertEqual(parsed['food'], 'cracker')
        self.assertEqual(parsed['amount'], 40)
        self.assertEqual(parsed['pieces'], None)
        self.assertEqual(parsed['size'], None)
        self.assertEqual(parsed['details'], False)
        self.assertEqual(parsed['serving'], None)

        parsed = message_parser('40g di cracker')
        self.assertEqual(parsed['food'], 'cracker')
        self.assertEqual(parsed['amount'], 40)
        self.assertEqual(parsed['pieces'], None)
        self.assertEqual(parsed['size'], None)
        self.assertEqual(parsed['details'], False)
        self.assertEqual(parsed['serving'], None)


        # ACE
        parsed = message_parser('ACE')
        self.assertEqual(parsed['food'], 'ace')
        self.assertEqual(parsed['amount'], None)
        self.assertEqual(parsed['pieces'], None)
        self.assertEqual(parsed['size'], None)
        self.assertEqual(parsed['details'], False)
        self.assertEqual(parsed['serving'], None)

        parsed = message_parser('un ACE')
        self.assertEqual(parsed['food'], 'ace')
        self.assertEqual(parsed['amount'], None)
        self.assertEqual(parsed['pieces'], 1)
        self.assertEqual(parsed['size'], None)
        self.assertEqual(parsed['details'], False)
        self.assertEqual(parsed['serving'], None)

        parsed = message_parser('un ACE piccolo')
        self.assertEqual(parsed['food'], 'ace')
        self.assertEqual(parsed['amount'], None)
        self.assertEqual(parsed['pieces'], 1)
        self.assertEqual(parsed['size'], 's')
        self.assertEqual(parsed['details'], False)
        self.assertEqual(parsed['serving'], None)

        parsed = message_parser('una porzione di ACE')
        self.assertEqual(parsed['food'], 'ace')
        self.assertEqual(parsed['amount'], None)
        self.assertEqual(parsed['pieces'], None)
        self.assertEqual(parsed['size'], None)
        self.assertEqual(parsed['details'], False)
        self.assertEqual(parsed['serving'], 1)

        parsed = message_parser('un bicchiere di ACE')
        self.assertEqual(parsed['food'], 'ace')
        self.assertEqual(parsed['amount'], None)
        self.assertEqual(parsed['pieces'], None)
        self.assertEqual(parsed['size'], None)
        self.assertEqual(parsed['details'], False)
        self.assertEqual(parsed['serving'], 1)

        parsed = message_parser('un bicchiere di ACE piccolo')
        self.assertEqual(parsed['food'], 'ace')
        self.assertEqual(parsed['amount'], None)
        self.assertEqual(parsed['pieces'], None)
        self.assertEqual(parsed['size'], 's')
        self.assertEqual(parsed['details'], False)
        self.assertEqual(parsed['serving'], 1)

        parsed = message_parser('200ml di ACE')
        self.assertEqual(parsed['food'], 'ace')
        self.assertEqual(parsed['amount'], 200)
        self.assertEqual(parsed['pieces'], None)
        self.assertEqual(parsed['size'], None)
        self.assertEqual(parsed['details'], False)
        self.assertEqual(parsed['serving'], None)

        parsed = message_parser('un bicchiere di succo di albicocca')
        self.assertEqual(parsed['food'], 'succo di albicocca')
        self.assertEqual(parsed['amount'], None)
        self.assertEqual(parsed['pieces'], None)
        self.assertEqual(parsed['size'], None)
        self.assertEqual(parsed['details'], False)
        self.assertEqual(parsed['serving'], 1)

        parsed = message_parser('un bicchiere di succo di albicocca grande')
        self.assertEqual(parsed['food'], 'succo di albicocca')
        self.assertEqual(parsed['amount'], None)
        self.assertEqual(parsed['pieces'], None)
        self.assertEqual(parsed['size'], 'l')
        self.assertEqual(parsed['details'], False)
        self.assertEqual(parsed['serving'], 1)

        parsed = message_parser('un bicchiere grande di succo di albicocca')
        self.assertEqual(parsed['food'], 'succo di albicocca')
        self.assertEqual(parsed['amount'], None)
        self.assertEqual(parsed['pieces'], None)
        self.assertEqual(parsed['size'], 'l')
        self.assertEqual(parsed['details'], False)
        self.assertEqual(parsed['serving'], 1)
