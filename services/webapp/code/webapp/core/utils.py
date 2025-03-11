import traceback
import logging
import requests

# Setup logging
logger = logging.getLogger(__name__)


def booleanize(*args, **kwargs):
    # Handle both single value and kwargs to get arg name
    name = None
    if args and not kwargs:
        value=args[0]
    elif kwargs and not args:
        for item in kwargs:
            name  = item
            value = kwargs[item]
            break
    else:
        raise Exception('Internal Error')

    # Handle shortcut: an arg with its name equal to ist value is considered as True
    if name==value:
        return True

    if isinstance(value, bool):
        return value
    else:
        if value.upper() in ('TRUE', 'YES', 'Y', '1'):
            return True
        else:
            return False


def format_exception(e):

    # Importing here instead of on top avoids circular dependencies problems when loading booleanize in settings
    from django.conf import settings

    if settings.DEBUG:
        # Cutting away the last char removed the newline at the end of the stacktrace 
        return str('Got exception "{}" of type "{}" with traceback:\n{}'.format(e.__class__.__name__, type(e), traceback.format_exc()))[:-1]
    else:
        return str('Got exception "{}" of type "{}" with traceback "{}"'.format(e.__class__.__name__, type(e), traceback.format_exc().replace('\n', '|')))


def get_index_name(prefix=None, variant=None):
    name = 'food'
    if prefix:
        name = '{}{}'.format(prefix, name)
    if variant:
        name = '{}_{}'.format(name, variant)
    return name


class SearchService():

    def __init__(self, host='search', index_prefix=None):
        self.host = host
        self.index_prefix = index_prefix

    def add(self, item, variant=None):

        index_name = get_index_name(self.index_prefix, variant)
        item['index_name'] = index_name # TODO: this is hack-ish
        logger.debug('Adding using index "%s"', index_name)

        url = 'http://{}/api/v1/add/'.format(self.host)
        response = requests.post(url, json=item)
        if not response.status_code == 200:
            raise Exception(response.content)

    def delete(self, item, variant=None):

        index_name = get_index_name(self.index_prefix, variant)
        item['index_name'] = index_name # TODO: this is hack-ish
        logger.debug('Deleting using index "%s"', index_name)

        url = 'http://{}/api/v1/delete/'.format(self.host)
        response = requests.post(url, json=item)
        if response.status_code not in [200, 404]:
            raise Exception(response.content)

    def query(self, q, variant=None, min_score=0.1, max_diff=0.3):

        q = q.replace(' ', '%20') # TODO: make it all url-safe

        index_name = get_index_name(self.index_prefix, variant)
        logger.debug('Querying using index "%s"', index_name)

        url = 'http://{}/api/v1/search?q={}&index_name={}&min_score={}&max_diff={}'.format(self.host, q, index_name, min_score, max_diff)
        response = requests.get(url)
        if not response.status_code == 200:
            raise Exception(response.content)
        else:
            return response.json()


def message_parser(message):

    # Prepare
    parsed = {}
    parsed['food'] = None
    parsed['amount'] = None
    parsed['pieces'] = None
    parsed['size'] = None
    parsed['details'] = False

    message = message.lower().strip()

    # Details?
    if message.endswith('con dettagli'):
        parsed['details'] = True
        message = message.replace('con dettagli', '')
        message = message.strip()
    if message.endswith('dettagli'):
        parsed['details'] = True
        message = message.replace('dettagli', '')
        message = message.strip()

    # Remove special chars and double white spaces
    message = message.replace('\'', ' ')
    message = message.replace('  ', ' ')
    message = message.replace('  ', ' ')

    # Split message in elements
    message_elements = message.split(' ')

    # Strip each element
    message_elements = [message_element.strip() for message_element in message_elements]

    # Parse pieces
    if not (message_elements[0].endswith('g') or (len(message_elements) > 1 and message_elements[1] == 'g')):
        piece_candidate = message_elements[0]
        piece_candidate = piece_candidate.lower()
        piece_candidate = piece_candidate.strip()

        if piece_candidate.isdigit():
            parsed['pieces'] = int(piece_candidate)
        else:
            if piece_candidate in ['un', 'uno', 'una']:
                parsed['pieces'] = 1
            if piece_candidate in ['due']:
                parsed['pieces'] = 2
            if piece_candidate in ['tre']:
                parsed['pieces'] = 3
            if piece_candidate in ['quattro']:
                parsed['pieces'] = 4
            if piece_candidate in ['cinque']:
                parsed['pieces'] = 5
            if piece_candidate in ['sei']:
                parsed['pieces'] = 6
            if piece_candidate in ['sette']:
                parsed['pieces'] = 7
            if piece_candidate in ['otto']:
                parsed['pieces'] = 8
            if piece_candidate in ['nove']:
                parsed['pieces'] = 9
            if piece_candidate in ['dieci']:
                parsed['pieces'] = 10

        if parsed['pieces'] :
            message = message.replace(message_elements[0], '').strip()

    # Parse amount or pieces
    if message_elements[0].endswith('g'):
        message_elements[0] = message_elements[0][0:-1]
        try:
            parsed['amount'] = int(message_elements[0])
        except:
            pass
        else:
            message = ' '.join(message_elements[1:])

    if len(message_elements) > 1 and message_elements[1] == 'g':
        try:
            parsed['amount'] = int(message_elements[0])
        except:
            pass
        else:
            message = ' '.join(message_elements[2:])

    # Parse size
    small_size_keywords = ['piccola', 'piccolo', 'piccoli', 'piccole', 'poco', 'poca', 'pochi']
    medium_size_keywords = ['media', 'medio', 'medi', 'medie']
    large_size_keywords = ['grande', 'grandi', 'tanta', 'tanto', 'tanti']

    for keyword in small_size_keywords:
        if message.startswith(keyword) or message.endswith(keyword):
            message = message.replace(keyword, '')
            message = message.strip()
            parsed['size'] = 's'
            break

    for keyword in medium_size_keywords:
        if message.startswith(keyword) or message.endswith(keyword):
            message = message.replace(keyword, '')
            message = message.strip()
            parsed['size'] = 'm'
            break

    for keyword in large_size_keywords:
        if message.startswith(keyword) or message.endswith(keyword):
            message = message.replace(keyword, '')
            message = message.strip()
            parsed['size'] = 'l'
            break

    # Set food now
    parsed['food'] = message

    # Return
    return parsed

