Simple example on how to instrument azure libraries using [opencensus](https://opencensus.io).

Example:
```
from oc_azure.msrest.trace import trace_integration
from opencensus.trace import tracer as tracer_module


# Initialize a tracer, by default using the `PrintExporter`
trace_integration()
tracer = tracer_module.Tracer()
tracer.span(name='main')

# Do stuff
print('doing stuff')

tracer.end_span()

```
