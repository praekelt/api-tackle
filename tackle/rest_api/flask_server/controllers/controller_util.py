"""
EXAMPLE - HTTP Controller referenced from example swagger spec.
"""

import flask
import logging
from typing import Union, Dict, List, Tuple, Optional, Any  # noqa # pylint: disable=unused-import
from functools import wraps
import threading
import copy

from tackle.rest_api import wrapper_util

JSONIterableType = Union[Dict[str, Any], List[Any]]
JSONType = Union[str, int, float, bool, None, JSONIterableType]


def api_key_auth(key, required_scopes=None):
    """
    Function pointed to by x-apikeyInfoFunc in the swagger security definitions.
    """
    if key is not None:
        # Pretty much a null implementation.
        return {'sub': 'unknown'}
    else:
        return None


def get_auth_token():
    """
    Retrieve the auth token provided in the request header. Allow both AUTH_TOKEN and X-Auth-Token headers.
    """
    auth_token = flask.request.headers.get('AUTH_TOKEN')

    if auth_token is None:
        auth_token = flask.request.headers.get('X-Auth-Token')

    return auth_token


def get_caller_name():
    """
    Retrieve the caller name provided in the request header.
    """
    caller_name = flask.request.headers.get('X-Caller')

    return caller_name


controller_decorator_call_count = 0
controller_decorator_call_count_lock = threading.Lock()


def controller_decorator(f):
    """
    Decorator to add usage header to response and to log info on the controller.
    """

    @wraps(f)
    def decorated_f(*args, **kwargs):
        global controller_decorator_call_count

        with controller_decorator_call_count_lock:
            controller_decorator_call_count += 1
            local_controller_decorator_call_count = copy.deepcopy(controller_decorator_call_count)

        logging.info(f"flask_controller_request: ({local_controller_decorator_call_count}) {f.__name__} <- {str(args)} {str(kwargs)}")

        # request_data = flask.request.data
        # remote_addr = flask.request.remote_addr
        # logging.info(f'flask_controller_request (raw data): "{request_data}" from {remote_addr}')

        response_json, response_code = f(*args, **kwargs)

        call_count_tuple = wrapper_util.auth_token_call_cache.get(get_auth_token())  # count, limit

        if call_count_tuple is not None:
            if call_count_tuple[1] is None:
                call_count_remaining = -1  # Implies unlimited remaining.
            else:
                call_count_remaining = max(call_count_tuple[1] - call_count_tuple[0], 0)  # Don't return a value <0
        else:
            call_count_remaining = 0  # Zero remaining; auth token not found?

        response_json_str = str(response_json)
        if len(response_json_str) > 300:
            response_json_str = response_json_str[:297] + '...'

        logging.info(f"flask_controller_response: ({local_controller_decorator_call_count}) {f.__name__} -> "
                     f"{str((response_json_str, response_code, {'X-RateLimit-Remaining': call_count_remaining}))}\n")

        return response_json, response_code, {"X-RateLimit-Remaining": call_count_remaining}

    return decorated_f
