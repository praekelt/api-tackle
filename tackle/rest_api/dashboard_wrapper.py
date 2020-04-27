"""
EXAMPLE - Wrapper of tackle's Dashboard Python API in HTTP API.
"""

from typing import Tuple, Optional  # noqa # pylint: disable=unused-import

from tackle.rest_api import wrapper_util
from tackle import __version__ as tackle_version


@wrapper_util.lock_decorator
@wrapper_util.auth_decorator
def get_details(auth_token: str,
                caller_name: Optional[str]) -> Tuple[int, wrapper_util.JSONType]:
    dash_content = {
        'api_version': tackle_version,
        'service_name': 'tackle Service',
        'log_file': wrapper_util.get_log_filename()
    }

    return 200, dash_content
