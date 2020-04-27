from prometheus_client import Gauge
from prometheus_client import start_http_server

import logging
import uuid

# RED:
# Rate - the number of requests, per second, you services are serving.
# Errors - the number of failed requests per second.
# Duration distribution - distributions of the amount of time each request takes.

promths_exec_id = uuid.uuid4()  # Unique ID for this Python kernel.


def create_prometheus_server(prometheus_port: int):
    print("Creating promethius server...", flush=True)
    logging.info(f"prometheus_utils.create_prometheus_server: Creating promethius server... ")
    start_http_server(prometheus_port)
    logging.info(f"prometheus_utils.create_prometheus_server: Done creating promethius server.")
    print("Done (creating promethius server).", flush=True)
    print()


class PrometheusLoggingHandler(logging.Handler):
    """ Custom logging handler to send error events to Prometheus. Meant to be used at log level of error."""

    def __init__(self):
        logging.Handler.__init__(self)

        # Counter of number of emitted events.
        self.promths_emit_count_gauge = Gauge('tackle_logging_emit_count',
                                              'tackle - Number of logging errors emitted.',
                                              ['exec_id', 'desc', 'msg'])

    def emit(self, record):
        try:
            if record.levelno >= logging.CRITICAL:
                self.promths_emit_count_gauge.labels(exec_id=promths_exec_id,
                                                     desc='critical',  # pylint: disable=no-member
                                                     msg=str(record.getMessage())).inc()  # pylint: disable=no-member
            elif record.levelno >= logging.ERROR:
                self.promths_emit_count_gauge.labels(exec_id=promths_exec_id,
                                                     desc='error',  # pylint: disable=no-member
                                                     msg=str(record.getMessage())).inc()  # pylint: disable=no-member
            elif record.levelno >= logging.WARNING:
                self.promths_emit_count_gauge.labels(exec_id=promths_exec_id,
                                                     desc='warning',  # pylint: disable=no-member
                                                     msg=str(record.getMessage())).inc()  # pylint: disable=no-member
            elif record.levelno >= logging.INFO:
                self.promths_emit_count_gauge.labels(exec_id=promths_exec_id,
                                                     desc='info',  # pylint: disable=no-member
                                                     msg=str(record.getMessage())).inc()  # pylint: disable=no-member
            elif record.levelno >= logging.DEBUG:
                self.promths_emit_count_gauge.labels(exec_id=promths_exec_id,
                                                     desc='debug',  # pylint: disable=no-member
                                                     msg=str(record.getMessage())).inc()  # pylint: disable=no-member
        except Exception:
            raise


# How much of the flask app's time is spent idle.
promths_flask_idle_fraction_gauge = Gauge('tackle_flask_idle_fraction',
                                          'tackle - Flask Idle Fraction',
                                          ['exec_id'])

# How much of the service wrapper's (and deeper) time is spent idle.
promths_wrapper_idle_fraction_gauge = Gauge('tackle_wrapper_idle_fraction',
                                            'tackle - Wrapper Idle Fraction',
                                            ['exec_id'])

# The instance's request latencies.
promths_request_latency_gauge = Gauge('tackle_request_latency_seconds',
                                      'tackle - Request Latency',
                                      ['exec_id', 'auth_desc', 'caller_name', 'endpoint'])

# The instance's number of unauthorised denied calls.
promths_call_count_gauge_unauthrsd = Gauge('tackle_unauthrsd_call_count',
                                           'tackle - Number of unauthorised & denied calls.',
                                           ['exec_id', 'auth_desc', 'caller_name'])

# The call count across all servers (cached locally, but updated regularly from the DB).
# May be used for billing!
promths_call_count_gauge_authrsd = Gauge('tackle_api_call_count',
                                         'tackle - API Call Count',
                                         ['exec_id', 'auth_desc', 'caller_name'])

# The instance's http responses
promths_http_response_gauge = Gauge('tackle_http_responses',
                                    'tackle - HTTP Responses.',
                                    ['exec_id', 'auth_desc', 'caller_name', 'endpoint', 'status'])
