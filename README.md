# Agents Observation

LLM agent with OpenTelemetry observability (traces, metrics, prompts/content) using GenAI semantic conventions.

**Which attributes are used?** See [docs/OTEL_ATTRIBUTES.md](docs/OTEL_ATTRIBUTES.md) for the full list and links to the official specs.

## OpenTelemetry setup

- **SDK**: Traces and metrics are produced by the OpenTelemetry Python SDK and sent to an OTLP collector over HTTP.
- **Instrumentation**: The OpenAI client (used by LangChain) is auto-instrumented with `opentelemetry-instrumentation-openai-v2`, which emits:
  - **Traces**: Spans for each LLM call with `gen_ai.*` attributes (operation, model, token usage, etc.) and optional prompt/response content.
  - **Metrics**: `gen_ai.client.operation.duration`, `gen_ai.client.token.usage` (when supported).
- **Content**: Prompts and completions are captured by default; set `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=false` or `init_telemetry(capture_content=False)` to disable.

### Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OTEL_EXPORTER_OTLP_ENDPOINT` | *(not set)* | OTLP HTTP base URL (e.g. `http://localhost:4318`). If unset, no export (no collector connection). |
| `OTEL_SEMCONV_STABILITY_OPT_IN` | `gen_ai_latest_experimental` | Use latest GenAI semantic conventions. |
| `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT` | `true` | Capture prompts and completions in spans. |

### Run the OTLP collector

Using the included config (receives on port 4318, prints to debug):

```bash
# With Docker
docker run -v "%cd%\otel-collector-config.yaml:/etc/otel/config.yaml" -p 4318:4318 otel/opentelemetry-collector-contrib:latest --config=/etc/otel/config.yaml
```

Set `OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318` and run the app; traces and metrics will be sent to the collector. If you don't set it, the app runs without exporting (no connection errors).
