# OpenTelemetry attributes used for LLM observability

This project uses **OpenTelemetry GenAI semantic conventions**. The instrumentation (`opentelemetry-instrumentation-openai-v2`) emits spans and metrics with the attributes below. Exact set depends on the instrumentation version and `OTEL_SEMCONV_STABILITY_OPT_IN=gen_ai_latest_experimental`.

## Where to see the full list

### 1. Official specs (definitions of every attribute)

- **GenAI attributes (all)**  
  https://opentelemetry.io/docs/specs/semconv/registry/attributes/gen-ai/

- **OpenAI-specific (spans + metrics)**  
  https://opentelemetry.io/docs/specs/semconv/gen-ai/openai

- **GenAI metrics** (e.g. `gen_ai.client.token.usage`, `gen_ai.client.operation.duration`)  
  https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-metrics/

### 2. What this app actually emits

The **OpenAI v2 instrumentor** sets attributes on **spans** (and optionally **events**) and reports **metrics**. Typical attributes you’ll see:

| Attribute | Description |
|-----------|-------------|
| `gen_ai.operation.name` | e.g. `chat` |
| `gen_ai.provider.name` | e.g. `openai` |
| `gen_ai.request.model` | Requested model name |
| `gen_ai.response.model` | Model that produced the response |
| `gen_ai.usage.input_tokens` | Prompt tokens |
| `gen_ai.usage.output_tokens` | Completion tokens |
| `gen_ai.input.messages` | Prompt/chat input (if `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=true`) |
| `gen_ai.output.messages` | Response content (same opt-in) |
| `gen_ai.system_instructions` | System prompt when captured |

Metrics include `gen_ai.client.operation.duration` and `gen_ai.client.token.usage` (with dimensions like `gen_ai.operation.name`, `gen_ai.provider.name`, `gen_ai.token.type`).

The **instrumentation source code** is the ground truth for which attributes are set in your setup:

- https://github.com/open-telemetry/opentelemetry-python-contrib/tree/main/instrumentation/opentelemetry-instrumentation-openai-v2

## Where to see attributes in practice

1. **Collector debug exporter**  
   With `otel-collector-config.yaml` and the `debug` exporter, the collector logs every span and metric (including all attributes) to stdout.

2. **Backend UIs**  
   If you export to Jaeger, Zipkin, Grafana Tempo, or similar, open a trace and inspect span attributes and events there.

3. **Console exporter (local dev)**  
   You can temporarily use `ConsoleSpanExporter` in `telemetry.py` to print spans (and their attributes) to the terminal instead of OTLP.
