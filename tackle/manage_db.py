from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager

import os
import sys

# NOTE: The below import is useful to bring tackle into the Python path!
module_path = os.path.abspath(os.path.join('..'))
print("module_path =", module_path)
if module_path not in sys.path:
    sys.path.append(module_path)

from tackle.flask_utils import db, create_flask_app  # noqa

from tackle.rest_api import get_path  # noqa

from tackle.db_models import APIKeyData  # noqa
from tackle.db_models import AdminAPIKeyData  # noqa
from tackle.db_models import APICallCountBreakdownData  # noqa

# Get the production or local DB URL from the OS env variable.
database_url = os.environ.get("TACKLE_DATABASE_URL",
                              'sqlite:///app.db')

if database_url is None:
    sys.exit("TACKLE_DATABASE_URL env variable is not configured. See the 'local_db' make target to create a local "
             "test database for URL postgresql://127.0.0.1:5432/tackle?user=tackle&password=tackle")

# wrapper_util.start_tackle_engine

# Create the flask app (without an API or UI) to activate the db.
flask_app = create_flask_app(specification_dir=get_path() + '/flask_server/swagger/',
                             add_api=False, swagger_ui=False,
                             database_url=database_url,
                             database_create_tables=False,
                             debug=True)

migrate = Migrate(flask_app.app, db)

manager = Manager(flask_app.app)
manager.add_command("db", MigrateCommand)

if __name__ == "__main__":
    manager.run()
