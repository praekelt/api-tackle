# import psutil
import time
import threading
from typing import List, Dict, Tuple, Any, Optional, Union
from functools import wraps
# from inspect import getfullargspec
# from datetime import datetime
import logging

from sqlalchemy.orm import load_only

from tackle.db_models import APIKeyData
from tackle.db_models import AdminAPIKeyData
from tackle.db_models import APICallCountBreakdownData

from tackle.flask_utils import db
from tackle.flask_utils import get_log_filename  # noqa # pylint: disable=unused-import

from tackle.prometheus_utils import promths_exec_id
from tackle.prometheus_utils import promths_wrapper_idle_fraction_gauge
from tackle.prometheus_utils import promths_request_latency_gauge
from tackle.prometheus_utils import promths_call_count_gauge_unauthrsd
from tackle.prometheus_utils import promths_call_count_gauge_authrsd
from tackle.prometheus_utils import promths_http_response_gauge

JSONType = Union[str, int, float, bool, None, Dict[str, Any], List[Any]]

# ToDo: Consider splitting this file into db_util.py and wrapper_util.py so that the db management can happen without having
#       to import wrapper things.

#
#  Module global variable that store if the default auth tokens have been lazily configured.
__default_auth_tokens_configured = False


# Lock for access to the single tackle instance defined in wrapper_util. Note: The lock is meant to protect against
# multi-threaded access and doesn't impact pre-forked multi-process execution!

__wrapper_lock = threading.Lock()


# =============================
# Cache of API call count and call count limit tuples (call_count, call_count_limit)
auth_token_call_cache = {}  # type: Dict[str, Tuple[int,Optional[int]]]
auth_token_desc_cache = {}  # type: Dict[str, str]

last_operation_start_time = 0.0
last_operation_end_time = 0.0


def lock_decorator(f):
    """
    Decorator to protect access to the wrapper_util trope instance and its wrapper functions
    using __trope_engine_wrapper_lock. NOTE: This lock is meant to queue concurrent access to the service wrapper.
    """

    @wraps(f)
    def decorated_f(*args, **kwargs):
        # pre_lock_time = time.time()

        # Optional param to not acquire a lock if you already might have one AND know what you are doing.
        acquire_lock: bool = kwargs.get('lock_decorator_acquire_lock', True)

        if acquire_lock is not False:
            __wrapper_lock.acquire()
            # start_time = time.time()
            # logging.info(f"lock_decorator_nlpe: __nlpe_wrapper_lock acquired in {start_time - pre_lock_time}s")
        # else:
        # start_time = time.time()
        # logging.info(f"lock_decorator_nlpe: __nlpe_wrapper_lock not requested!")

        try:
            response_code, response_json = f(*args, **kwargs)
        except Exception as e:
            caller_name = kwargs.get('caller_name')

            logging.exception(f"lock_decorator_trope: Uncaught exception: {e}! caller_name = {caller_name}")

            promths_http_response_gauge.labels(exec_id=promths_exec_id,
                                               auth_desc=f"[Uncaught exception: {str(e)}]",
                                               caller_name=caller_name,
                                               endpoint=f.__name__, status=500).inc()  # pylint: disable=no-member
            raise  # re-raise the uncaught exception.
        finally:  # call release when try block is finished or before uncaught exceptions raised.
            if acquire_lock is not False:
                __wrapper_lock.release()

            # end_time = time.time()
            # logging.info(f"lock_decorator_nlpe: __nlpe_wrapper_lock duration = {round(end_time - start_time, 4)}s  "
            #              f"end_time = {datetime.now()}")

        return response_code, response_json

    return decorated_f


def auth_decorator(f):
    """
    Decorator to check that an auth token was provided and that it is valid and
    to log info on the wrapper layer functions.
    """

    # ToDo: Is this decorator thread safe??? Not currently at least due to how last_operation_end_time is used.

    @wraps(f)
    def decorated_f(*args, **kwargs):
        global last_operation_start_time
        global last_operation_end_time

        current_time = time.time()

        if last_operation_end_time != 0.0:
            idle_time = round(current_time - last_operation_end_time, 4)
            total_time = round(current_time - last_operation_start_time, 4)
            promths_wrapper_idle_fraction_gauge.labels(exec_id=promths_exec_id).set(idle_time / total_time)

        last_operation_start_time = current_time

        # === Find auth_token amongst the named parameters ===
        auth_token = kwargs.get('auth_token')
        # ====================================================
        caller_name = kwargs.get('caller_name')

        # if 'image' in f.__name__:
        #     logging.info(f"rest_wrapper_request: {f.__name__ } <- [arguments not shown] (caller_name={caller_name})")
        # else:
        #     logging.info(f"rest_wrapper_request: {f.__name__} <- {str(args)} {str(kwargs)}")

        # === Check that an auth token was provided ===
        if auth_token is None:
            promths_call_count_gauge_unauthrsd.labels(exec_id=promths_exec_id,
                                                      auth_desc="None",
                                                      caller_name=caller_name).inc()  # pylint: disable=no-member
            logging.info(f"auth_decorator: None: No authorisation token provided!")
            last_operation_end_time = time.time()
            return 403, {"error_detail": "No authorisation token provided!"}  # Bad/Malformed request.
        # =============================================

        auth_desc = auth_token_desc_cache.get(auth_token, "[Not in cache!]")

        # === Check that the auth token is valid ===
        # First DB access for the request ...
        if not is_auth_token_valid(auth_token):  # Note: Also updates the local call count cache!
            logging.info(f"auth_decorator: {auth_token}: Invalid authorisation token or API rate limit exceeded!")
            promths_call_count_gauge_unauthrsd.labels(exec_id=promths_exec_id,
                                                      auth_desc=auth_desc,
                                                      caller_name=caller_name).inc()  # pylint: disable=no-member
            last_operation_end_time = time.time()
            return 403, {"error_detail": "Invalid authorisation token provided or API rate limit exceeded!"}
        # ==========================================

        # === Update desc. to latest cached value after update in is_auth_token_valid ^ ===
        auth_desc = auth_token_desc_cache.get(auth_token, "[Not in cache!]")
        # =================================================================================

        start_time = time.time()

        # === Call the wrapper layer function ===
        response_code, response_json = f(*args, **kwargs)
        # =======================================

        call_duration = round(time.time() - start_time, 4)

        # logging.info(f"rest_wrapper_response: {f.__name__} -> {str((response_code, response_json))} "
        #              f"in {call_duration} seconds.")

        promths_http_response_gauge.labels(exec_id=promths_exec_id,
                                           auth_desc=auth_desc,
                                           caller_name=caller_name,
                                           endpoint=f.__name__, status=response_code).inc()  # pylint: disable=no-member

        if 200 <= response_code <= 299:
            # The API call was successful - Update call count & log/monitor.

            text = kwargs.get('text')

            # === Count one call unit per 100 chars of text ===
            if text is None:
                call_units = 1
            else:
                call_units = int(len(text) / 100 + 1)
            # =================================================

            increment_auth_token_call_count(auth_token, call_units,  # Count one API call per call unit.
                                            f.__name__)

            # promths_request_histogrm.labels(endpoint=f.__name__).observe(call_duration)  # pylint: disable=no-member
            promths_request_latency_gauge.labels(exec_id=promths_exec_id,
                                                 auth_desc=auth_desc,
                                                 caller_name=caller_name,
                                                 endpoint=f.__name__).set(call_duration)  # pylint: disable=no-member

            call_count, call_count_limit = auth_token_call_cache.get(auth_token, (0, None))
            # promths_call_units_histogrm.labels(endpoint=f.__name__).observe(call_units)  # pylint: disable=no-member
            promths_call_count_gauge_authrsd.labels(exec_id=promths_exec_id,
                                                    auth_desc=auth_desc,
                                                    caller_name=caller_name).set(call_count)  # pylint: disable=no-member

            logging.info(f"cached_call_count = {auth_token_call_cache.get(auth_token)}, "
                         f"cached_desc = {auth_desc}, caller_name = {caller_name}")

        last_operation_end_time = time.time()

        return response_code, response_json

    return decorated_f


def add_auth_token(auth_token: str, desc: Optional[str],
                   call_count_limit: Optional[int] = None,
                   call_count_limit_relative: bool = False) -> bool:
    """
    Add or update an auth token to the DB. Local cache will be updated during next API request in is_auth_token_valid(...)!

    :param auth_token: The auth token to add/update.
    :param desc: The description to apply to the token. 'None' to leave existing description unchanged.
    :param call_count_limit: The call count limit to place on the token. 'None' to make unlimited.
    :param call_count_limit_relative: If True then the limit will be relative to the current count. Default is False!
    :return: True/False indicating success of operation.
    """
    try:
        query = db.session.query(APIKeyData)
        instance = query.get(ident=auth_token)

        if instance:
            if desc is not None:
                instance.desc = desc

            # Initialise the call_count if None.
            if instance.call_count is None:
                instance.call_count = 0

            if (call_count_limit is None) or (call_count_limit_relative is False):
                instance.call_count_limit = call_count_limit
            else:
                instance.call_count_limit = instance.call_count + call_count_limit
        else:
            instance = APIKeyData(auth_token, str(desc), 0, call_count_limit)
            db.session.add(instance)

        db.session.commit()
        return True
    except Exception:
        db.session.rollback()
        raise
    finally:
        db.session.close()


def remove_auth_token(auth_token: str) -> bool:
    """
    Removes an auth token.

    :param auth_token: The auth token to remove.
    :return: True/False indicating success of operation.
    """
    try:
        query = db.session.query(APIKeyData)
        instance = query.get(ident=auth_token)

        if instance:
            db.session.delete(instance)
            db.session.commit()
            success = True
        else:
            success = False

        # Remove breakdown call counts for this auth token.
        query = db.session.query(APICallCountBreakdownData)
        rows = query.filter_by(auth_key=auth_token).all()

        if rows:
            for row in rows:
                db.session.delete(row)
            db.session.commit()

        return success
    except Exception:
        db.session.rollback()
        raise
    finally:
        db.session.close()


def load_auth_token_list() -> List[str]:
    """
    Get the list of auth tokens stored in the DB.

    :return: List[str]
    """
    query = db.session.query(APIKeyData)
    query = query.options(load_only("auth_key"))

    api_key_object_list = query.all()
    auth_token_list = []

    for instance in api_key_object_list:
        auth_token_list.append(instance.auth_key)

    db.session.close()

    return auth_token_list


def get_auth_token_details(auth_token: str) -> Optional[Dict]:
    """
    Gets the desc, call_count and call_count_limit of an auth token.

    :param auth_token: The auth token to get the details of.
    :return: None if auth token not found, else {desc, call_count, call_count_limit}
    """
    query = db.session.query(APIKeyData)
    instance = query.get(ident=auth_token)

    auth_token_details = None  # type: Optional[Dict]

    if instance:
        desc = instance.desc
        call_count = instance.call_count
        call_count_limit = instance.call_count_limit

        if call_count is None:
            call_count = 0

        auth_token_details = {"desc": desc,
                              "call_count": call_count,
                              "call_count_limit": call_count_limit}

        # Get call count breakdown.
        query = db.session.query(APICallCountBreakdownData)
        rows = query.filter_by(auth_key=auth_token).all()

        if rows:
            breakdown_dict = {}
            for row in rows:
                breakdown_dict[row.endpoint] = row.call_count
            auth_token_details['call_count_breakdown'] = breakdown_dict

    db.session.close()
    return auth_token_details


def add_admin_auth_token(auth_token: str, desc: str) -> bool:
    """ Add or update an admin auth_token to the DB. """
    try:
        query = db.session.query(AdminAPIKeyData)
        instance = query.get(ident=auth_token)

        if instance:
            instance.desc = desc
        else:
            instance = AdminAPIKeyData(auth_token, desc)
            db.session.add(instance)

        db.session.commit()
        return True
    except Exception:
        db.session.rollback()
        raise
    finally:
        db.session.close()


def remove_admin_auth_token(auth_token: str) -> bool:
    """
    Removes an admin auth token.

    :param auth_token: The auth token to remove.
    :return: True/False indicating success of operation.
    """
    try:
        query = db.session.query(AdminAPIKeyData)
        instance = query.get(ident=auth_token)

        if instance:
            db.session.delete(instance)
            db.session.commit()
            success = True
        else:
            success = False

        return success
    except Exception:
        db.session.rollback()
        raise
    finally:
        db.session.close()


def load_admin_auth_token_list() -> List[str]:
    """
    Get the list of adminauth tokens stored in the DB.

    :return: List[str]
    """
    query = db.session.query(AdminAPIKeyData)
    query = query.options(load_only("auth_key"))

    api_key_object_list = query.all()
    auth_token_list = []

    for instance in api_key_object_list:
        auth_token_list.append(instance.auth_key)

    db.session.close()

    return auth_token_list


def add_default_auth_tokens():
    """ Add some known auth tokens to the DB for ease of dev and use. """
    # add_admin_auth_token('...', "Admin & Testing.")
    # add_auth_token('...', "Admin & Testing.")
    pass


def is_auth_token_valid(auth_token: str) -> bool:
    """
    Checks if the auth token is a valid token and that its rate limit has not been exceeded. Also
    updates the local call count and API key desc caches with the info from the DB.

    :param auth_token: The auth token.
    :return: True only if the token is a valid token and its rate limit has not been exceeded.
    """

    global __default_auth_tokens_configured

    try:
        # Check if the default tokens have been initialised.
        if not __default_auth_tokens_configured:
            add_default_auth_tokens()
            __default_auth_tokens_configured = True

        query = db.session.query(APIKeyData)
        # query = query.options(load_only("auth_key", "desc", "call_count", "call_count_limit"))

        instance = query.get(ident=auth_token)

        # 1 - Initialise call_count if None.
        if instance and instance.call_count is None:
            # Token valid, but call_count not assigned yet.
            instance.call_count = 0
            db.session.commit()

        # 2 - Update the local call count cache which is updated and used later to build response headers, etc.
        if instance:
            auth_token_call_cache[auth_token] = (instance.call_count, instance.call_count_limit)
            auth_token_desc_cache[auth_token] = instance.desc
        else:
            auth_token_call_cache.pop(auth_token, None)
            auth_token_desc_cache.pop(auth_token, None)

        # 3 - Check that token is valid and rate limit (if any) not exceeded.
        if instance and \
                ((instance.call_count_limit is None) or
                 (instance.call_count < instance.call_count_limit)):
            # Token valid AND (no rate limit OR rate limit not exceeded).
            valid = True
        else:
            valid = False

        return valid
    except Exception:
        db.session.rollback()
        raise
    finally:
        db.session.close()


def increment_auth_token_call_count(auth_token: str, units: int,
                                    endpoint: Optional[str] = None):
    """
    Increments the call count for the auth token - increments the DB and the local cache.

    :param auth_token: The auth token.
    :param units: The number of units of use.
    :param endpoint: The endpoint to allocate the call count to.
    """
    try:
        # Atomic update of call_count in DB.
        query = db.session.query(APIKeyData)
        query.filter_by(auth_key=auth_token).update({'call_count': APIKeyData.call_count + units})
        db.session.commit()

        # Update of the local call cache.
        cached_call_count_tuple = auth_token_call_cache.get(auth_token)
        if cached_call_count_tuple is not None:
            auth_token_call_cache[auth_token] = (cached_call_count_tuple[0] + units, cached_call_count_tuple[1])

        if endpoint is not None:
            # Atomic update of call count breakdown in DB.
            query = db.session.query(APICallCountBreakdownData)
            row_count = \
                query.filter_by(auth_key=auth_token,
                                endpoint=str(endpoint)
                                ).update({'call_count': APICallCountBreakdownData.call_count + units})

            if row_count == 0:
                # Add the key,endpoint row if not yet present.
                instance = APICallCountBreakdownData(auth_token, endpoint, units)
                db.session.add(instance)

            db.session.commit()

    except Exception:
        db.session.rollback()
        raise
    finally:
        db.session.close()


def is_admin_auth_token_valid(auth_token: str) -> bool:
    global __default_auth_tokens_configured

    # Check if the default tokens have been initialised.
    if not __default_auth_tokens_configured:
        add_default_auth_tokens()
        __default_auth_tokens_configured = True

    query = db.session.query(AdminAPIKeyData)
    query = query.options(load_only("auth_key"))

    instance = query.get(ident=auth_token)

    if instance:
        valid = True
    else:
        valid = False

    db.session.close()
    return valid
