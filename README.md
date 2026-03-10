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

### Where to observe prompts and messages (contents)

**Prompts and completions** are in **traces** (span attributes like `gen_ai.input.messages`, `gen_ai.output.messages`, `gen_ai.system_instructions`), not in Prometheus. You can see them in:

| Where | How |
|-------|-----|
| **Jaeger UI** | With docker-compose, start Jaeger and open **http://localhost:16686**. Run a search, open a trace, then open a span → **Tags** (or **Process**) to see attributes including prompt/message content. |
| **Collector logs** | Traces are also sent to the `debug` exporter. Run `docker-compose logs -f otel-collector` to see span dumps (including attributes) in stdout. |

The collector is configured to send traces to **Jaeger** so you get a UI; it also logs them with the debug exporter.

### Prometheus (metrics only)

**Prometheus stores metrics only, not traces.** Metrics (e.g. `gen_ai.client.operation.duration`, `genai_genai_agent_invocations_total`) are exposed by the collector and scraped by Prometheus at http://localhost:9090. Traces (and their prompt/message content) are in Jaeger or the collector logs, not in Prometheus.

### Run the OTLP collector

Config receives OTLP on 4318 and exposes metrics for Prometheus on 8889:

```powershell
# PowerShell (4318 = OTLP, 8889 = Prometheus scrape)
docker run -v "${PWD}/otel-collector-config.yaml:/etc/otel/config.yaml" -p 4318:4318 -p 8889:8889 otel/opentelemetry-collector-contrib:latest --config=/etc/otel/config.yaml
```

```cmd
# CMD
docker run -v "%cd%\otel-collector-config.yaml:/etc/otel/config.yaml" -p 4318:4318 -p 8889:8889 otel/opentelemetry-collector-contrib:latest --config=/etc/otel/config.yaml
```

### Docker Compose (app + collector + Prometheus + Jaeger)

From the project root, with a `.env` file that has `OPENAI_API_KEY` and `OPENAI_MODEL`:

```bash
# Start Jaeger, collector, and Prometheus (start Jaeger to see traces and prompts/messages)
docker-compose up -d jaeger otel-collector prometheus

# Run the app interactively (sends telemetry to the collector)
docker-compose run --rm -it app
```

- **Prometheus (metrics):** http://localhost:9090  
- **Jaeger (traces + prompts/messages):** http://localhost:16686 → Search → pick a service (e.g. `weather-time-agent`) → open a trace → open a span and check **Tags** for `gen_ai.input.messages`, `gen_ai.output.messages`, etc.



