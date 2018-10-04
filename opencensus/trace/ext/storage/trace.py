import logging
import wrapt

from opencensus.trace import attributes_helper
from opencensus.trace import execution_context
from opencensus.trace import span as span_module

import azure.storage.common.storageclient

client = azure.storage

log = logging.getLogger(__name__)

MODULE_NAME = 'azure.storage'

SERVICECLIENT_WRAP_METHODS = [ '_perform_request' ]

def trace_integration(tracer=None):
    """Wrap the msrest library to trace it."""
    log.info('Integrated module: {}'.format(MODULE_NAME))
    execution_context.set_opencensus_tracer(tracer)

    for name in SERVICECLIENT_WRAP_METHODS:
        # Wrap msrest.ServiceClient class
        wrapt.wrap_function_wrapper(
            MODULE_NAME, 'common.storageclient.StorageClient.{}'.format(name), wrap_serviceclient_request)


def wrap_serviceclient_request(wrapped, instance, args, kwargs):
    tracer = execution_context.get_opencensus_tracer()
    with tracer.span('{}.request'.format(type(instance).__name__)) as span:
        request = args[0] # Request is the first argument passed in
        client_request_id = request.headers.get('x-ms-client-request-id', None)
        if client_request_id:
            span.add_attribute('x-ms-client-request-id', client_request_id)
        span.add_attribute('AccountName', instance.account_name)
        span.add_attribute('http.url', request.path)
        span.add_attribute('http.method', request.method)
        result = wrapped(*args, **kwargs)

    return result

