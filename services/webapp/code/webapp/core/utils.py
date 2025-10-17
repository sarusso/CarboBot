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

    def query(self, q, variant=None, min_score=0.1, max_diff=0.3, see_also=False):

        # Remove unnecessary articles
        q_without_articles = q
        for article in ['con', 'coi', 'la', 'le', 'gli', 'i', 'alle', 'all\'', 'l\'']:
            if ' {} '.format(article) in q:
                q_without_articles = q_without_articles.replace(' {} '.format(article), ' ')
        for contracted_article in ['all\'', 'l\'']:
            if ' {}' .format(contracted_article) in q:
                q_without_articles = q_without_articles.replace(' {}'.format(contracted_article), '')

        q_cleaned = q_without_articles.replace(' ', '%20') # TODO: make it all url-safe

        index_name = get_index_name(self.index_prefix, variant)
        logger.debug('Querying using index "%s" for "%s" and min_score=%s, max_diff=%s', index_name, q_cleaned, min_score, max_diff)

        url = 'http://{}/api/v1/search?q={}&index_name={}&min_score={}&max_diff={}&see_also={}'.format(self.host,
                                                                                                       q_cleaned,
                                                                                                       index_name,
                                                                                                       min_score,
                                                                                                       max_diff,
                                                                                                       see_also)
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
    parsed['serving'] = None

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

    # Standardize a few things (or maybe warn about common errors?)
    for size_keyword in ['piccolo', 'piccola', 'piccoli', 'poco', 'poca', 'pochi'
                         'medio', 'media', 'medi', 'media',
                         'grande', 'grandi', 'tanto', 'tanta', 'tanti']:
        if ' {} '.format(size_keyword) in message:
            message = message.replace(' {} '.format(size_keyword), ' ')
            message = message + ' {}'.format(size_keyword)
            break

    # Split message in elements
    message_elements = message.split(' ')

    # Strip each element
    message_elements = [message_element.strip() for message_element in message_elements]

    # Parse serving
    if len(message_elements) >=3 \
    and not (message_elements[0].endswith('g') or (len(message_elements) >= 1 and message_elements[1] == 'g')) \
    and not (message_elements[0].endswith('ml') or (len(message_elements) >= 1 and message_elements[1] == 'ml')):

        serving_candidate = message_elements[0] + ' ' + message_elements[1]
        serving_candidate = serving_candidate.lower()
        serving_candidate = serving_candidate.strip()
        if serving_candidate in ['porzione di', 'pacchetto di', 'confezione di', 'bicchiere di']:
            parsed['serving'] = 1
            message = message.replace(serving_candidate, '').strip()

        serving_candidate = message_elements[0] + ' ' + message_elements[1] + ' ' + message_elements[2]
        serving_candidate = serving_candidate.lower()
        serving_candidate = serving_candidate.strip()
        if serving_candidate in ['una porzione di', 'un pacchetto di', 'una confezione di', 'un bicchiere di']:
            parsed['serving'] = 1
            message = message.replace(serving_candidate, '').strip()

    # Re-split if a serving was found
    if parsed['serving']:
        message_elements = message.split(' ')

    # Parse pieces
    if len(message_elements) >=2 \
    and not (message_elements[0].endswith('g') or (len(message_elements) > 1 and message_elements[1] == 'g')) \
    and not (message_elements[0].endswith('ml') or (len(message_elements) > 1 and message_elements[1] == 'ml')):
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

    # Re-split if a number of pieces was found
    if parsed['pieces']:
        message_elements = message.split(' ')

    # Remove unnecessary stuff
    if message_elements[0] == 'di':
        message_elements = message_elements[1:]
        message = ' '.join(message_elements)

    # Parse amount (g)
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

    # Parse amount (ml)
    if message_elements[0].endswith('ml'):
        message_elements[0] = message_elements[0][0:-2]
        try:
            parsed['amount'] = int(message_elements[0])
        except:
            pass
        else:
            message = ' '.join(message_elements[1:])

    if len(message_elements) > 1 and message_elements[1] == 'ml':
        try:
            parsed['amount'] = int(message_elements[0])
        except:
            pass
        else:
            message = ' '.join(message_elements[2:])

    # Re-split if an amount was found
    if parsed['amount']:
        message_elements = message.split(' ')

    # Remove unnecessary stuff
    if message_elements[0] == 'di':
        message_elements = message_elements[1:]
        message = ' '.join(message_elements)

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

