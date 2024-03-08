import traceback
import logging

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


def log_user_activity(level, msg, request, caller=None):

    # Get the caller function name through inspect with some logic
    #import inspect
    #caller =  inspect.stack()[1][3]
    #if caller == "post":
    #    caller =  inspect.stack()[2][3]

    try:
        msg = str(caller) + " view - USER " + str(request.user.email) + ": " + str(msg)
    except AttributeError:
        msg = str(caller) + " view - USER UNKNOWN: " + str(msg)

    try:
        level = getattr(logging, level)
    except:
        raise

    logger.log(level, msg)

