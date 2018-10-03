import logging
import wrapt

from opencensus.trace import attributes_helper
from opencensus.trace import execution_context
from opencensus.trace import span as span_module

import msrest
import msrest.paging
import msrest.polling

log = logging.getLogger(__name__)

MODULE_NAME = 'msrest'

SERVICECLIENT_WRAP_METHODS = [ 'send' ]
PAGED_WRAP_METHODS = ['advance_page']

HTTP_URL = attributes_helper.COMMON_ATTRIBUTES['HTTP_URL']
HTTP_STATUS_CODE = attributes_helper.COMMON_ATTRIBUTES['HTTP_STATUS_CODE']


def trace_integration(tracer = None):
    """Wrap the msrest library to trace it."""
    log.info('Integrated module: {}'.format(MODULE_NAME))

    execution_context.set_opencensus_tracer(tracer)

    for name in SERVICECLIENT_WRAP_METHODS:
        # Wrap msrest.ServiceClient class
        wrapt.wrap_function_wrapper(
            MODULE_NAME, 'ServiceClient.{}'.format(name), wrap_serviceclient_request)

    for name in PAGED_WRAP_METHODS:
        # Wrap msrest.Pagedclass
        wrapt.wrap_function_wrapper(
            MODULE_NAME + '.paging', 'Paged.{}'.format(name), wrap_paged_request)

    wrapt.wrap_function_wrapper('msrest', 'polling.LROPoller.__init__', wrap_poller_init)
    wrapt.wrap_function_wrapper('msrest', 'polling.LROPoller._start', wrap_poller_start)


def wrap_serviceclient_request(wrapped, instance, args, kwargs):
    tracer = execution_context.get_opencensus_tracer()
    with tracer.span('ServiceClient.request') as span:
        request = args[0] # Request is the first argument passed in
        client_request_id = request.headers.get('x-ms-client-request-id', instance.config.headers.get('x-ms-client-request-id', None))
        if client_request_id:
            span.add_attribute('x-ms-client-request-id', client_request_id)
        span.add_attribute(HTTP_URL, request.url)
        span.add_attribute('http.method', request.method)
        result = wrapped(*args, **kwargs)
        span.add_attribute(HTTP_STATUS_CODE, str(result.status_code))
        
        try: 
            span.add_attribute('http.header.retry-after', str(result.headers['Retry-After']))
        except KeyError:
            pass

    return result


def wrap_paged_request(wrapped, instance, args, kwargs):
    tracer = execution_context.get_opencensus_tracer()
    with tracer.span('[msrest]paging') as span:
        result = wrapped(*args, **kwargs)
    return result


def wrap_poller_init(wrapped, instance, args, kwargs):
    tracer = execution_context.get_opencensus_tracer()
    # Since the actual polling occurs on a separate thread, we need to stash it away in the poller instance
    # so we can access it from said thread
    setattr(instance, '_opencensus_tracer', tracer)
    wrapped(*args, **kwargs)


def wrap_poller_start(wrapped, instance, args, kwargs):
    # Pick up the tracer associated with the poller (if any) and associate it with the current context
    tracer = getattr(instance, '_opencensus_tracer', None)
    execution_context.set_opencensus_tracer(tracer)
    with tracer.span('[msrest]polling'):
        result = wrapped(*args, **kwargs)
    return result
