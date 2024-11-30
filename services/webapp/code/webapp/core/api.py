import os
import requests
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.response import Response

# Setup logging
logger = logging.getLogger(__name__)


TELEGRAM_TOKEN =  os.environ.get('TELEGRAM_TOKEN', None)


def ok200(caller=None, data=None):
    return Response({"status": "OK", "data": data}, status=status.HTTP_200_OK)


class TelegramClient():

    def __init__(self, token):
        if not token:
            raise ValueError('Empty Telegram client token')
        self.token = token

    def send_message(self, chat_id, text):
        url = 'https://api.telegram.org/bot{}/sendMessage'.format(self.token)
        payload = {
                    'chat_id': chat_id,
                    'text': text,
                    'parse_mode': 'markdown'
                    }
        requests.post(url,json=payload)


class TelegramAPI(APIView):

    def post(self, request):

        telegram_client = TelegramClient(TELEGRAM_TOKEN)

        # {
        #   "update_id": 342022349,
        #   "message": {
        #     "message_id": 1,
        #     "from": {
        #       "id": 400123452,
        #       "is_bot": false,
        #       "first_name": "The Ross",
        #       "username": "ross",
        #       "language_code": "en"
        #     },
        #     "chat": {
        #       "id": 400123452,
        #       "first_name": "The Ross",
        #       "username": "ross",
        #       "type": "private"
        #     },
        #     "date": 1678372916,
        #     "text": "/start",
        #     "entities": [
        #       {
        #         "offset": 0,
        #         "length": 6,
        #         "type": "bot_command"
        #       }
        #     ]
        #   }
        # }

        telegram_chat_id = request.data['message']['chat']['id']
        message = request.data['message']['text'].strip()
        logger.debug('Received message: %s', message)
        telegram_client.send_message(telegram_chat_id, 'Received message: *"{}"*')

        return ok200('OK')

