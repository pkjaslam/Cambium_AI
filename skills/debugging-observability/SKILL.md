---
name: debugging-observability
description: >
  Designs observability stacks and guides disciplined debugging of running systems.
  Use when a service is failing in production, a performance regression appeared, an
  incident needs a root cause, or the team needs to instrument a new system. Trigger on:
  "production issue", "debug this", "why is it slow", "add logging", "set up Prometheus",
  "trace this request", "SLO breach", "error spike", "structured logging", "OpenTelemetry",
  "LLM tracing". Pairs well with software-architecture (instrument what you designed) and
  software-testing-qa (tests reproduce the bug; traces explain the mechanism).
  Boundary: observability reveals symptoms and narrows the search space. The human
  interprets the signals and decides the fix. Cambium does not access live production
  systems or secrets.
---

# You Cannot Fix What You Cannot See

Observability is not monitoring. Monitoring tells you when something is wrong. Observability
lets you ask arbitrary questions about a system's internal state from its external outputs.
Build for both. The three pillars (logs, metrics, traces) answer different questions:
logs say what happened, metrics say how often and how much, traces say where time went.

---

## The Three Pillars

| Pillar | Answers | Tool examples | Cardinality |
|---|---|---|---|
| Structured logs | What happened and in what context | OpenTelemetry Collector, Loki, CloudWatch | Low to medium |
| Metrics | How much, how fast, how often over time | Prometheus + Grafana, Datadog | Low (aggregated) |
| Distributed traces | Where did this request spend time across services | OpenTelemetry + Tempo, Jaeger, Zipkin | High |

Instrument all three from the start. Retrofitting observability into an uninstrumented
system during an incident is the worst time to do it.

---

## OpenTelemetry First

Use OpenTelemetry (OTEL) as the instrumentation layer and keep the backend swappable.
Vendor lock-in at the instrumentation layer is painful and unnecessary.

```python
# Minimal OTEL setup for a Python service
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

provider = TracerProvider()
provider.add_span_processor(
    BatchSpanProcessor(OTLPSpanExporter(endpoint="http://otel-collector:4317"))
)
trace.set_tracer_provider(provider)
tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("process-analysis") as span:
    span.set_attribute("analysis.id", analysis_id)
    result = run_analysis(analysis_id)
```

For LLM pipelines, use OpenLLMetry (Traceloop) to capture prompt tokens, latency,
model version, and cost per call without writing custom instrumentation.

---

## Structured Logging

Log JSON. Never log free-form strings in a production service. Free-form strings cannot
be queried, aggregated, or alerted on reliably.

```python
import structlog

log = structlog.get_logger()
log.info(
    "analysis_completed",
    analysis_id=analysis_id,
    duration_ms=duration_ms,
    model="gpt-4o",
    token_count=response.usage.total_tokens,
)
```

Every log event should carry: timestamp, severity, trace ID (for correlation with spans),
service name, and the business event name. Add context, not noise.

---

## SLIs and SLOs

An SLI (Service Level Indicator) is a measured ratio. An SLO (Service Level Objective)
is the target. Define them before something breaks.

| SLI | Example query (Prometheus) | SLO |
|---|---|---|
| Availability | `rate(http_requests_total{code!~"5.."}[5m]) / rate(http_requests_total[5m])` | 99.5% over 30 days |
| Latency | `histogram_quantile(0.95, rate(http_duration_seconds_bucket[5m]))` | p95 < 500 ms |
| Error rate | `rate(http_requests_total{code=~"5.."}[5m])` | < 0.5% |

Track error budget. When it is exhausted, stop new features and fix reliability.

---

## Disciplined Debugging Method

Follow this sequence. Skipping steps wastes time.

1. **Reproduce.** Can you trigger the bug reliably in a non-production environment? If not,
   add instrumentation first and wait for recurrence. Never debug blind.
2. **Isolate.** Narrow to the smallest failing case. Remove irrelevant variables. Use
   binary search on inputs and config if the trigger is not obvious.
3. **Hypothesize.** State a falsifiable cause. "I think X is failing because of Y." Write
   it down. Do not start changing code before you have a hypothesis.
4. **Bisect.** If the bug is a regression, use `git bisect` or compare metric timelines
   to the deploy that introduced it. Correlation with a deploy is strong evidence.
5. **Fix and verify.** Change one thing. Confirm the bug is gone. Confirm no regression
   in surrounding tests. Write a test that would have caught this earlier.

---

## Honest Guardrails

- Cambium designs dashboards, writes instrumentation code, and interprets sample traces
  you share. It does not connect to live production systems or read secrets.
- Observability narrows hypotheses; it does not always point to a single root cause.
  Distributed systems can have multiple concurrent causes for one symptom.
- Metrics and traces are sampled in high-traffic systems. A missing trace does not mean
  the request succeeded; it may mean it was dropped from the sample.
- SLOs are agreements, not guarantees. Setting an SLO you cannot measure is worse than
  having none.

---

## Attribution and Sources

- OpenTelemetry (CNCF project, vendor-neutral instrumentation standard).
  https://opentelemetry.io/docs/
- OpenLLMetry by Traceloop (LLM pipeline tracing built on OTEL).
  https://github.com/traceloop/openllmetry
- Prometheus metrics (CNCF). https://prometheus.io/docs/introduction/overview/
- Grafana dashboards and alerting. https://grafana.com/docs/grafana/latest/
- Google SRE Book, "Service Level Objectives" chapter (free online).
  https://sre.google/sre-book/service-level-objectives/
- Charity Majors, Liz Fong-Jones, George Miranda, "Observability Engineering" (O'Reilly 2022).
- structlog (Python structured logging). https://www.structlog.org/en/stable/
