import os
import time
from unittest.mock import patch
from django.test import TestCase
from ..utils import SearchService, load_foods_from_csv
from ..bot import Bot
from .testing_utils import get_or_create_user, reset_test_indexes, delete_test_indexes

# Note: these are end-to-end tests, using two other services in chain (search and elastic)

class TestBot(TestCase):

    @classmethod
    def setUpClass(cls):
        reset_test_indexes()
        test_user = get_or_create_user('testuser')
        csv_path = os.path.join(os.path.dirname(__file__), 'test_data.csv')
        search_service = SearchService(index_prefix='test_')
        load_foods_from_csv(csv_path, test_user, search_service=search_service)
        time.sleep(1)
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        delete_test_indexes()
        super().tearDownClass()

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_bot_answer_exact_match(self):
        bot = Bot()
        reply = bot.answer('cornflakes')
        self.assertIn('cornflakes', reply.lower())
        self.assertIn('87g', reply)

    def test_bot_answer_search(self):
        bot = Bot()
        test_search_service = SearchService(index_prefix='test_')
        with patch('webapp.core.models.SearchService', return_value=test_search_service):
            reply = bot.answer('pasta integrale poco condita')
        self.assertIn('pasta integrale', reply.lower())
        self.assertIn('carboidrati', reply)

    def test_bot_answer_search_portions(self):
        bot = Bot()
        test_search_service = SearchService(index_prefix='test_')
        with patch('webapp.core.models.SearchService', return_value=test_search_service):
            reply = bot.answer('pane integrale')
            self.assertIn('Una porzione media', reply)
            reply = bot.answer('pasta')
            self.assertIn('Per avere informazioni sulle porzioni', reply)

    def test_bot_answer_search_exact_match(self):
        bot = Bot()
        test_search_service = SearchService(index_prefix='test_')
        with patch('webapp.core.models.SearchService', return_value=test_search_service):
            reply = bot.answer('pane integrale fresco')
            self.assertIn('Ho trovato "*pane integrale fresco/*"', reply)

