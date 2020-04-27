# """Unit test base class for the api-tackle Python Module."""
# import unittest
#
# from tackle.flask_utils import create_flask_app, db
# from tackle.flask_utils import setup_logging, reset_logging
#
#
# class BaseTestCase(unittest.TestCase):
#     def setUp(self):
#         setup_logging()
#
#         # Local DB for testing - See 'local_db' make target.
#         # database_url = "postgresql://127.0.0.1:5432/test_tackle?user=tackle&password=tackle"
#         database_url = 'sqlite:///app.db'
#
#         # Create the flask app to activate the db for all unit tests.
#         flask_app = create_flask_app(add_api=False, swagger_ui=False,
#                                      database_url=database_url,
#                                      database_create_table=True,
#                                      debug=True)
#
#     def tearDown(self):
#         db.session.remove()
#         db.drop_all()
#
#         reset_logging()
