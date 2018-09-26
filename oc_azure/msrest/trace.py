# Copyright 2017, OpenCensus Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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

SERVICECLIENT_WRAP_METHODS = [ 'send' ] # ['close', 'send_formdata', 'send', 'stream_download', 'get', 'put', 'post', 'patch', 'delete', 'head', 'merge']
PAGED_WRAP_METHODS = ['advance_page']
POLLING_WRAP_METHODS = [ ]

HTTP_URL = attributes_helper.COMMON_ATTRIBUTES['HTTP_URL']
HTTP_STATUS_CODE = attributes_helper.COMMON_ATTRIBUTES['HTTP_STATUS_CODE']


def trace_integration():
    """Wrap the msrest library to trace it."""
    log.info('Integrated module: {}'.format(MODULE_NAME))

    for name in SERVICECLIENT_WRAP_METHODS:
        # Wrap msrest.ServiceClient class
        wrapt.wrap_function_wrapper(
            MODULE_NAME, '[msrest]ServiceClient.{}'.format(name), wrap_serviceclient_request)

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
        span.add_attribute('http.url', request.url)
        span.add_attribute('http.method', request.method)
        result = wrapped(*args, **kwargs)
        span.add_attribute('http.status_code', str(result.status_code))
        span.add_attribute('http.header.retry-after', str(result.headers.get('Retry-After', 'missing')))

    return result

def wrap_paged_request(wrapped, instance, args, kwargs):
    tracer = execution_context.get_opencensus_tracer()
    with tracer.span('[msrest]paging') as span:
        result = wrapped(*args, **kwargs)
    return result

def wrap_poller_init(wrapped, instance, args, kwargs):
    tracer = execution_context.get_opencensus_tracer()
    setattr(instance, '_opencensus_tracer', tracer)
    wrapped(*args, **kwargs)

def wrap_poller_start(wrapped, instance, args, kwargs):
    tracer = getattr(instance, '_opencensus_tracer', None)
    execution_context.set_opencensus_tracer(tracer)
    with tracer.span('[msrest]polling'):
        result = wrapped(*args, **kwargs)
    return result
