# Imports
from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from .utils import format_exception
from .exceptions import ErrorMessage, ConsistencyError

# Setup logging
import logging
logger = logging.getLogger(__name__)

# Public view
def public_view(wrapped_view):
    def public_view_wrapper(request, *argv, **kwargs):
        try:
            # Call the view
            return wrapped_view(request, *argv, **kwargs)

        except Exception as e:
            if isinstance(e, ErrorMessage):
                error_text = str(e)
            else:

                # Log the exception 
                logger.error(format_exception(e))

                # Raise the exception if we are in debug mode
                if settings.DEBUG:
                    raise

                # Otherwise, mask it
                else:
                    error_text = 'something went wrong ({})'.format(e)

            data = {'user': request.user,
                    'title': 'Error',
                    'error' : 'Error: "{}"'.format(error_text)}

            return render(request, 'error.html', {'data': data})
    return public_view_wrapper

# Private view
def private_view(wrapped_view):
    def private_view_wrapper(request, *argv, **kwargs):
        if request.user.is_authenticated:
            try:
                # Call the view
                return wrapped_view(request, *argv, **kwargs)

            except Exception as e:
                if isinstance(e, ErrorMessage):
                    error_text = str(e)
                else:

                    # Log the exception 
                    logger.error(format_exception(e))

                    # Raise the exception if we are in debug mode
                    if settings.DEBUG:
                        raise

                    # Otherwise, mask it
                    else:
                        error_text = 'something went wrong ({})'.format(e)

                data = {'user': request.user,
                        'title': 'Error',
                        'error' : 'Error: "{}"'.format(error_text)}

                return render(request, 'error.html', {'data': data})

        else:
            logger.debug('Setting cookie-based post login redirect to "%s"', request.build_absolute_uri())
            response = HttpResponseRedirect('/login')
            response.set_cookie('post_login_redirect', request.build_absolute_uri())
            return response

    return private_view_wrapper
