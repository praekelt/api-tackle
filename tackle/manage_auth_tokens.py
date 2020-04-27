"""
API Tackle - Example of how to manage auth token.
"""

import os
import sys

# NOTE: The below import is useful to bring tackle into the Python path!
module_path = os.path.abspath(os.path.join('.'))
print("module_path =", module_path)
if module_path not in sys.path:
    sys.path.append(module_path)

from tackle.flask_utils import create_flask_app  # noqa
from tackle.flask_utils import setup_logging  # noqa

from tackle.rest_api import get_path  # noqa

# from tackle.rest_api.wrapper_util import add_auth_token  # noqa
# from tackle.rest_api.wrapper_util import remove_admin_auth_token  # noqa
# from tackle.rest_api.wrapper_util import get_auth_token_details  # noqa
from tackle.rest_api.wrapper_util import load_auth_token_list  # noqa
from tackle.rest_api.wrapper_util import load_admin_auth_token_list  # noqa

# from tackle.rest_api.wrapper_util import start_wrapper_engine  # noqa


def main():
    setup_logging(requested_logging_path="~/.tackle/logs")

    # Get the production or local URL from the OS env variable.
    database_url = os.environ.get("TACKLE_DATABASE_URL",
                                  'sqlite:///app.db')

    if database_url is None:
        sys.exit("TACKLE_DATABASE_URL env variable is not configured. See the 'local_db' make target to create a local "
                 "test database for URL postgresql://127.0.0.1:5432/tackle?user=tackle&password=tackle")

    # start_wrapper_engine(...)

    # Create the flask app (without an API or UI) to activate the db.
    # flask_app = \
    create_flask_app(specification_dir=get_path() + '/flask_server/swagger/',
                     add_api=False,
                     swagger_ui=False,
                     database_url=database_url,
                     database_create_tables=False,
                     debug=True)

    print("Admin auth token list...")
    print(load_admin_auth_token_list())
    print()

    print("Auth token list...")
    print(load_auth_token_list())
    print()

    # print("Removing & Adding auth tokens...")
    #
    # print(remove_admin_auth_token('f6e8286f...'))
    #
    # # Add auth token with absolute call limit.
    # add_auth_token('cec15695d7...', "Test token", 5000)  # desc, free calls.
    # print(get_auth_token_details('cec15695d7...'))
    #
    # # Add auth token with call limit relative to current call count.
    # add_auth_token('dcg15695d7...', "Test token", 5000, True)  # desc, free calls (relative).
    # print(get_auth_token_details('dcg15695d7...'))

    print("done.")
    print()


if __name__ == '__main__':
    main()
