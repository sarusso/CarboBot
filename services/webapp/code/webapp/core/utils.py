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


class SearchService():

    def __init__(self, host='search', index=None):
        self.host = host
        self.index = index

    def add(self, item):
        if self.index is not None:
            item['index_name'] = self.index
            logger.debug('Using index "%s"', self.index)
        url = 'http://{}/api/v1/add/'.format(self.host)
        response = requests.post(url, json=item)
        if not response.status_code == 200:
            raise Exception(response.content)

    def delete(self, item):
        if self.index is not None:
            item['index_name'] = self.index
            logger.debug('Using index "%s"', self.index)
        url = 'http://{}/api/v1/delete/'.format(self.host)
        response = requests.post(url, json=item)
        if not response.status_code == 200:
            raise Exception(response.content)

    def query(self, q, min_score=0.1, max_diff=0.3):
        q = q.replace(' ', '%20') # TODO: make it all url-safe
        if self.index is not None:
            logger.debug('Using index "%s"', self.index)
            url = 'http://{}/api/v1/search?q={}&index_name={}&min_score={}&max_diff={}'.format(self.host, q, self.index, min_score, max_diff)
        else:
            url = 'http://{}/api/v1/search?q={}min_score={}&max_diff={}'.format(self.host, q, min_score, max_diff)
        response = requests.get(url)
        if not response.status_code == 200:
            raise Exception(response.content)
        else:
            return response.json()


