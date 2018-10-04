Simple example on how to instrument azure libraries using [opencensus](https://opencensus.io).

Example:
```
from opencensus.trace import tracer as tracer_module, config_integration


# Initialize a tracer, by default using the `PrintExporter`
tracer = tracer_module.Tracer()
config_integration.trace_configurations(['azure.msrest', 'azure.storage'], tracer=tracer)
tracer.span(name='main')

# Do stuff
print('doing stuff')

tracer.end_span()

```
