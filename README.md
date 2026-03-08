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

### Prometheus (metrics only)

**Prometheus stores metrics only, not traces.** So:

- **Metrics** (e.g. `gen_ai.client.operation.duration`, `gen_ai.client.token.usage`) → the collector exposes them in Prometheus format; Prometheus scrapes `http://<collector>:8889/metrics`.
- **Traces** (including **contents and messages** in span attributes) → do *not* go to Prometheus. They stay in the collector (debug exporter logs them) or you send them to a trace backend (e.g. Grafana Tempo, Jaeger) by uncommenting an OTLP trace exporter in `otel-collector-config.yaml`.

So you can use Prometheus for metrics and a separate backend for traces (with contents/messages).

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

### Docker Compose (app + collector + Prometheus)

From the project root, with a `.env` file that has `OPENAI_API_KEY` and `OPENAI_MODEL`:

```bash
# Start collector and Prometheus (and build the app image)
docker-compose up -d otel-collector prometheus

# Run the app interactively (sends telemetry to the collector)
docker-compose run --rm -it app
```

Then open **http://localhost:9090** for the Prometheus UI. The compose file uses `prometheus-docker.yml` so Prometheus scrapes the collector by service name.

**Prometheus shows “no data” for GenAI metrics?**

1. **Metrics expire when the app stops** – The collector’s Prometheus exporter **drops metrics after a few minutes** with no new data. So if you run the app, make one request, then stop the app and look at Prometheus later, those metrics are often already gone. **Do this instead:** run the app, ask 1–2 questions, then **within 1–2 minutes** in Prometheus run:  
   `genai_genai_agent_invocations_total`  
   (This counter is emitted by the app on every agent call and is the most reliable way to see data.)

2. **Avoid `rate([5m])` right after a short run** – `rate(...[5m])` needs multiple samples in the last 5 minutes. After a brief run, use the raw counter first:  
   `genai_genai_agent_invocations_total`

3. **Check scrape targets** – **Status → Targets**: `otel-collector:8889` should be **UP**. If `up` works but GenAI metrics don’t, the app likely hasn’t sent metrics recently; run the app again and query within 1–2 minutes.

### Run without Docker Compose

Point Prometheus at the collector (example `prometheus.yml` is for running Prometheus on the host):

```yaml
scrape_configs:
  - job_name: "otel-collector"
    static_configs:
      - targets: ["localhost:8889"]
```

Set `OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318` and run the app; traces and metrics go to the collector, and Prometheus can scrape metrics from port 8889. If you don't set the endpoint, the app runs without exporting (no connection errors).

