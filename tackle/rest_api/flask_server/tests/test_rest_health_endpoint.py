# import unittest
import time

from tackle.rest_api.flask_server.tests import BaseTestCase, send_request_check_response
from tackle.rest_api import get_path


# @unittest.skip("skipping during dev")
class TestRestHealthEndpoint(BaseTestCase):
    def __init__(self, *args, **kwargs):
        BaseTestCase.__init__(self,
                              *args,
                              specification_dir=get_path() + '/flask_server/swagger/',
                              requested_logging_path="~/.tackle/logs",
                              **kwargs)

    def test_health_endpoint(self):
        print("Rest HTTP test_health_endpoint:")
        start_time = time.time()

        response_check = send_request_check_response(self.client, "/health", "get",
                                                     {},
                                                     200,
                                                     {},
                                                     treat_list_as_set=True)

        self.assertTrue(response_check)

        print('time = ' + str(time.time() - start_time))
