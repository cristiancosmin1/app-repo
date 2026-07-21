import os

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


def setup_telemetry(app, engine):
    resource = Resource.create(
        {
            "service.name": os.getenv(
                "OTEL_SERVICE_NAME",
                "shopping-app",
            ),
            "deployment.environment": "local",
        }
    )

    provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(provider)

    endpoint = os.getenv(
        "OTEL_EXPORTER_OTLP_ENDPOINT",
        "http://localhost:4318",
    )

    exporter = OTLPSpanExporter(
        endpoint=f"{endpoint}/v1/traces",
    )

    provider.add_span_processor(
        BatchSpanProcessor(exporter)
    )

    FastAPIInstrumentor.instrument_app(app)

    SQLAlchemyInstrumentor().instrument(
        engine=engine,
    )

    return trace.get_tracer("shopping-app")
