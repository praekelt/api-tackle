#!/usr/bin/env python3

import os
import logging
import time

import connexion
# from connexion.resolver import RestyResolver

from typing import List, Optional, Dict  # noqa # pylint: disable=unused-import
from flask_sqlalchemy import SQLAlchemy
from flask_sqlalchemy import __version__ as __sqlalchemy_version__
from flask_cors import CORS
from flask import request

from tackle.prometheus_utils import promths_exec_id
from tackle.prometheus_utils import PrometheusLoggingHandler
from tackle.prometheus_utils import promths_flask_idle_fraction_gauge

LOGGERS_TO_IGNORE = [
    "connexion.operations.swagger2",
    "swagger_spec_validator.ref_validators",
    "connexion.operation",
    "connexion.apis.abstract",
    "connexion.apis.flask_api",
    "connexion.app",
    "connexion.decorators.validation",
    "connexion.decorators.parameter",
    "werkzeug",
    "matplotlib"
]  # type: List[str]

db = SQLAlchemy()

_logging_details = {}  # type: Dict


def get_log_filename() -> Optional[str]:
    return _logging_details.get("filename")


def reset_logging():
    """ Remove the handlers and filters from the logger to prevent, for example,
    handlers stacking up over multiple runs."""
    root = logging.getLogger()

    for handler in list(root.handlers):  # list(...) makes a copy of the handlers list.
        root.removeHandler(handler)
        handler.close()

    for filter in list(root.filters):  # list(...) makes a copy of the handlers list.
        root.removeFilter(filter)


def setup_logging(requested_logging_path: Optional[str] = None,
                  include_prometheus: bool = False):
    """ Setup logging to file and stderr. """
    global _logging_details

    reset_logging()

    # Set all loggers to 'ignore' to show only ERROR level logs or higher.
    for LOGGER in LOGGERS_TO_IGNORE:
        logging.getLogger(LOGGER).setLevel("ERROR")

    logger = logging.getLogger()  # Root logger.

    # Log Levels!:
    # CRITICAL 50
    # ERROR    40
    # WARNING  30
    # INFO     20
    # DEBUG    10
    # NOTSET    0

    logger.setLevel(logging.DEBUG)

    _logging_details["filename"] = "tackle_" + str(time.strftime("%Y-%m-%d")) + "_" + \
                                   str(time.strftime("%Hh%Mm%Ss")) + ".log"

    # Create formatter and add it to the handlers.
    formatter = logging.Formatter('%(asctime)s, %(name)s, %(levelname)s, %(message)s')

    # Create console handler.
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    if requested_logging_path is not None:
        # Create the logging path if it doesn't already exist.
        logging_path = os.path.expanduser(requested_logging_path)
        os.makedirs(logging_path, exist_ok=True)

        fh = logging.FileHandler(logging_path + "/" + _logging_details["filename"])
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    if include_prometheus:
        # Create Prometheus handler - sends number of WARNINGS+ to prometheus!
        ph = PrometheusLoggingHandler()
        ph.setLevel(logging.WARNING)
        ph.setFormatter(formatter)
        logger.addHandler(ph)

    logging.info(f"flask_utils.setup_logging: Logging started!")


def _setup_db(connexion_app: connexion.FlaskApp):
    """Setup and activate the DB within the Flask app."""
    db.init_app(connexion_app.app)
    connexion_app.app.app_context().push()  # Binds the app context to the current context.
    logging.info(f"flask_utils._setup_db: sqlalchemy.__version__ = {__sqlalchemy_version__}.")


def _setup_api(connexion_app: connexion.FlaskApp, debug: bool, swagger_ui: bool):
    """Setup the rest API within the Flask app."""
    connexion_app.add_api(specification='swagger.yaml',
                          arguments={'title': 'This is the HTTP API for tackle.'},
                          options={"debug": debug, "swagger_ui": swagger_ui})


last_operation_start_time = 0.0
last_operation_end_time = 0.0


def cllbck_before_flask_request():
    global last_operation_start_time
    global last_operation_end_time

    current_time = time.time()

    body_text = str(request.get_data())

    logging.info("flask_utils.cllbck_before_flask_request: ")  # Indicate start of new request.
    logging.info(f"flask_utils.cllbck_before_flask_request: "
                 f"body = {body_text[:47] + '...' if len(body_text) > 50 else body_text} "
                 f"auth header = {str(request.headers.get('X-Auth-Token'))}")

    if last_operation_end_time != 0.0:
        idle_time = round(current_time - last_operation_end_time, 4)
        total_time = round(current_time - last_operation_start_time, 4)
        promths_flask_idle_fraction_gauge.labels(exec_id=promths_exec_id).set(idle_time / total_time)

    last_operation_start_time = current_time


def cllbck_after_flask_request(response):
    global last_operation_end_time

    last_operation_end_time = time.time()
    return response


def create_flask_app(specification_dir: str,
                     add_api: bool,
                     swagger_ui: bool,
                     database_url: str,
                     database_create_tables: bool,
                     debug: bool):
    """
    Create the  Flask/Connexion app and the Flask-SQLAlchemy DB interface.
    The swagger spec is used to build an API if add_api == True!
    """
    print("Creating flask app...", flush=True)
    app = connexion.App(import_name=__name__,
                        specification_dir=specification_dir,
                        debug=debug)

    app.app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False  # Remove significant overhead from track modifications.
    app.app.config["SQLALCHEMY_DATABASE_URI"] = database_url

    if debug:
        app.app.config['TESTING'] = True
        # app.app.config["SQLALCHEMY_ECHO"] = True

    print("  _setup_db...", flush=True)
    _setup_db(app)

    print("  _setup_api...", flush=True)
    if add_api:
        _setup_api(app, debug=debug, swagger_ui=swagger_ui)

    print("Done (creating flask app).", flush=True)
    print()

    app.app.before_request(cllbck_before_flask_request)
    app.app.after_request(cllbck_after_flask_request)

    # add CORS support
    CORS(app.app)

    if database_create_tables:
        db.create_all()

    return app
