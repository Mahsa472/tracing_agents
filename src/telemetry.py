"""
OpenTelemetry setup for LLM observability: traces, metrics, and prompt/content capture.
Uses GenAI semantic conventions and sends data to an OTLP collector via HTTP.
"""
import os
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter


# GenAI semantic conventions opt-in (latest experimental attributes)
# Set before importing instrumentors so they emit gen_ai.* attributes
if "OTEL_SEMCONV_STABILITY_OPT_IN" not in os.environ:
    os.environ["OTEL_SEMCONV_STABILITY_OPT_IN"] = "gen_ai_latest_experimental"

# Capture prompts and completions in spans (opt-in for privacy)
if "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT" not in os.environ:
    os.environ["OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT"] = "true"


def init_telemetry(
    service_name: str = "agents-observation",
    otlp_endpoint: str | None = None,
    capture_content: bool = True,
) -> None:
    """
    Initialize OpenTelemetry: tracer and meter with OTLP HTTP exporters,
    then instrument the OpenAI client (used by LangChain) for GenAI spans and metrics.
    """
    if not capture_content:
        os.environ["OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT"] = "false"

    # Only export to OTLP when an endpoint is set (avoids connection errors when no collector is running)
    endpoint = (
        otlp_endpoint
        or os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
        or os.environ.get("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT")
    )
    # Build base URL and full per-signal URLs (collector expects /v1/traces and /v1/metrics)
    base_url = None
    if endpoint:
        endpoint = endpoint.strip()
        if endpoint.rstrip("/").endswith("/v1/traces"):
            base_url = endpoint.rsplit("/v1/traces", 1)[0].rstrip("/")
        elif endpoint.rstrip("/").endswith("/v1/metrics"):
            base_url = endpoint.rsplit("/v1/metrics", 1)[0].rstrip("/")
        else:
            base_url = endpoint.rstrip("/")
        traces_endpoint = f"{base_url}/v1/traces"
        metrics_endpoint = f"{base_url}/v1/metrics"

    resource = Resource.create({"service.name": service_name})

    # Traces
    trace_provider = TracerProvider(resource=resource)
    if base_url:
        trace_provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=traces_endpoint)))
    trace.set_tracer_provider(trace_provider)

    # Metrics
    if base_url:
        metric_reader = PeriodicExportingMetricReader(
            OTLPMetricExporter(endpoint=metrics_endpoint),
            export_interval_millis=10_000,
        )
        meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    else:
        meter_provider = MeterProvider(resource=resource)
    metrics.set_meter_provider(meter_provider)

    # Instrument OpenAI (LangChain's ChatOpenAI uses it under the hood)
    try:
        from opentelemetry.instrumentation.openai_v2 import OpenAIInstrumentor
        OpenAIInstrumentor().instrument()
    except Exception as e:
        # If openai_v2 not installed or incompatible, skip instrumentation
        import warnings
        warnings.warn(f"OpenAI instrumentation skipped: {e}", stacklevel=0)


# Lazy-initialized counter so we always have at least one metric in Prometheus
_agent_invocation_counter = None


def record_agent_invocation() -> None:
    """Call once per agent invocation so Prometheus shows a reliable counter (genai_agent_invocations_total)."""
    global _agent_invocation_counter
    try:
        provider = metrics.get_meter_provider()
        if _agent_invocation_counter is None:
            meter = provider.get_meter("agents-observation", "0.1.0")
            _agent_invocation_counter = meter.create_counter(
                name="genai_agent_invocations_total",
                description="Total number of agent invocations",
                unit="1",
            )
        _agent_invocation_counter.add(1)
    except Exception:
        pass


def shutdown_telemetry() -> None:
    """Flush and shutdown trace and metric providers."""
    try:
        trace.get_tracer_provider().force_flush()
    except Exception:
        pass
    try:
        metrics.get_meter_provider().force_flush()
    except Exception:
        pass
