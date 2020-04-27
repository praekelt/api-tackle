"""
EXAMPLE - Wrapper of tackle's Dashboard Python API in HTTP API.
"""

from typing import Tuple, Optional  # noqa # pylint: disable=unused-import
import logging

from tackle.rest_api import wrapper_util


@wrapper_util.lock_decorator
@wrapper_util.auth_decorator
def get_status(auth_token: str, caller_name: Optional[str]) -> Tuple[int, wrapper_util.JSONType]:
    logging.info(f"health_wrapper.health_get_status: Checking ...")

    # HEALTH: This is executed post auth so at least the auth DB is up and working.
    # However, some additional deeper health check may be done here as needed...
    # ...

    # No exceptions thrown up to this point so health is probably OK.
    logging.info(f"health_wrapper.health_get_status: OK!")

    return 200, {}  # Return 200 if no exceptions thrown on this typical API call path.
