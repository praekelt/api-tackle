# import unittest
import time

from tackle.rest_api.flask_server.tests import BaseTestCase, send_request_check_response
from tackle import __version__ as tackle_version
from tackle.rest_api import get_path


# @unittest.skip("skipping during dev")
class TestRestDashboard(BaseTestCase):
    def __init__(self, *args, **kwargs):
        BaseTestCase.__init__(self,
                              *args,
                              specification_dir=get_path() + '/flask_server/swagger/',
                              requested_logging_path="~/.tackle/logs",
                              **kwargs)

    def test_dashboard(self):
        print("Rest HTTP test_dashboard:")
        start_time = time.time()

        # Test the dashboard response.
        response_check = send_request_check_response(self.client, "/dashboard", "get",
                                                     {},
                                                     200,
                                                     {
                                                         'api_version': tackle_version,
                                                         'service_name': 'tackle Service'
                                                     },
                                                     treat_list_as_set=True)

        self.assertTrue(response_check)

        print('time = ' + str(time.time() - start_time))
