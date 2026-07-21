import os

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


def setup_telemetry(app, engine):
    print(">>> setup_telemetry() EXECUTED <<<")

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

    print(">>> TracerProvider:", trace.get_tracer_provider())

    endpoint = os.getenv(
        "OTEL_EXPORTER_OTLP_ENDPOINT",
        "http://localhost:4318",
    )

    print(">>> OTLP endpoint:", endpoint)

    exporter = OTLPSpanExporter(
        endpoint=f"{endpoint}/v1/traces",
    )

    provider.add_span_processor(
        BatchSpanProcessor(exporter)
    )

    print(">>> FastAPI instrumentation...")

    FastAPIInstrumentor.instrument_app(app)

    print(">>> SQLAlchemy instrumentation...")

    SQLAlchemyInstrumentor().instrument(
        engine=engine,
    )

    print(">>> OpenTelemetry initialization complete <<<")

    return trace.get_tracer("shopping-app")
