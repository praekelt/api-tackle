"""
EXAMPLE - HTTP Controller referenced from example swagger spec.
"""

from tackle.rest_api.flask_server.controllers import controller_util
from tackle.rest_api import dashboard_wrapper


@controller_util.controller_decorator
def get_details(user, token_info):
    return get_details_impl(user, token_info)


@controller_util.controller_decorator
def get_details_with_params(user, token_info,
                            params):
    return get_details_with_params_impl(user, token_info, params)


def get_details_impl(user, token_info):
    auth_token = controller_util.get_auth_token()
    caller_name = controller_util.get_caller_name()

    response_code, response_json = dashboard_wrapper.get_details(auth_token=auth_token,
                                                                 caller_name=caller_name)
    return response_json, response_code


def get_details_with_params_impl(user, token_info,
                                 params):
    # show_... = params.get("show_...")

    auth_token = controller_util.get_auth_token()
    caller_name = controller_util.get_caller_name()

    response_code, response_json = dashboard_wrapper.get_details(auth_token=auth_token,
                                                                 caller_name=caller_name)
    return response_json, response_code
