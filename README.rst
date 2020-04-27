API Tackle - Simple Python REST API Framework:
**********************************************

Quickstart
----------

.. code-block:: python

    """ WSGI Flask App for production hosting with e.g.: gunicorn --bind 0.0.0.0:80 -w 1 -t 120 wsgi """
    import os
    import logging

    from tackle.flask_utils import create_flask_app  # noqa
    from tackle.flask_utils import setup_logging  # noqa
    from tackle.prometheus_utils import create_prometheus_server  # noqa
    from tackle.rest_api.wrapper_util import add_auth_token  # noqa

    from tropical.rest_api import get_path  # noqa

    create_prometheus_server(9100)

    setup_logging(requested_logging_path='~/.tackle/logs',
                  include_prometheus=True)

    flask_app = create_flask_app(specification_dir=get_path() + '',
                                 add_api=True,
                                 swagger_ui=True,
                                 database_url='sqlite://',
                                 database_create_tables=True,
                                 debug=False)

    # === Add some auth tokens to the DB ===
    add_auth_token('tackleb6-12dd-4104-a7b6-f7d369ff5fec', "Default token e.g. internal hosting.")
    # === ===

    logging.info(f"rest_wsgi_app.py: __name__ == {__name__}")
    application = flask_app.app

    if __name__ == "__main__":
        logging.info(f"rest_wsgi_app.py: __main__ Starting Flask app in Python __main__ .")
        flask_app.run()


Building your own API
---------------------
...

