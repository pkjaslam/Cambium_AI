# Component 2: Performance & Cost Economics — Deep Evaluation

> **Evaluator:** Analysis of Cambium v1.9.3 token costs, runtime performance, latency, throughput, scalability, and infrastructure economics.
>
> **Verdict:** Cambium is **cheap to run** (cents to dollars per project) but **expensive to scale** (no caching, no connection pooling, no database, no horizontal scaling). It is designed for the **solo researcher on a laptop**, not a **university with 1,000 concurrent students**. The cost model is honest but incomplete — it tracks spending but does not prevent overspending.

---

## 1. Executive Summary

| Dimension | Grade | Why |
|---|---|---|
| **Token Cost per Project** | B+ | Honest pricing, per-agent cost tracking, Smart-Tier routing — but only Claude, no open-source alternatives |
| **Cost Control & Budgeting** | C | Logs cost but does not enforce budget caps; no cost alerts; no pre-run cost prediction |
| **Latency per Agent Call** | C | 120s timeout, no latency histograms, no SLA, no async/await for API calls |
| **Throughput (Concurrent Users)** | D | Max 5 concurrent sessions; single-user architecture; no database |
| **Scalability** | D | No horizontal scaling, no caching, no queueing, no load balancer |
| **Memory & Resource Footprint** | C | Lightweight Python runtime, but no memory profiling, no resource limits |
| **Cold Start Time** | B | Fast Python startup, but first API call is cold (no connection pooling) |
| **Infrastructure Economics** | D | No CDN, no edge caching, no database, no auto-scaling |
| **Cost Transparency** | A | Per-agent cost logging, honest FAQ, enforcement study budget published |
| **Performance Benchmarks** | D | No benchmarks, no load tests, no stress tests, no performance regression CI |

**Overall Performance & Cost Grade: C** — Cheap for one user, expensive to scale. The cost model works for early adopters but breaks at institutional scale.

---

## 2. Token Cost per Project

### What Exists

**Per-agent cost tracking:**
```python
# tools/cambium_run.py lines 21-24
PRICE = {"claude-opus-4-8": (15.0, 75.0), "claude-sonnet-4-6": (3.0, 15.0), "claude-haiku-4-5-20251001": (0.80, 4.0)}
def estimate_cost(model, usage):
    pin, pout = PRICE.get(model, (3.0, 15.0))
    return round(usage.get("input_tokens", 0)/1e6*pin + usage.get("output_tokens", 0)/1e6*pout, 6)
```

**Cost logging to CSV:**
```python
# tools/cambium_run.py lines 143-145
log_cost(os.path.join(ROOT, "agent_outputs", "cost_log.csv"),
         [runlbl, current_phase["id"], name, model, usage.get("input_tokens", 0),
          usage.get("output_tokens", 0), wall, cost])
```

**Smart-Tier model routing:**
- `strong` (Opus 4.8): Critical path — theory, stats, audit, referee, conduct, final writing
- `mid` (Sonnet 4.6): Breadth — scouts, labs, execution, pre-award, reporting
- `light` (Haiku 4.5): Bulk — cleanup, formatting, digests

### The Honest Cost Breakdown

Based on the enforcement study's per-run estimate (~1,300 input + ~900 output tokens) and the typical project flow:

| Project Type | Agents Mobilized | Model Mix | Est. Tokens | Est. Cost |
|---|---|---|---|---|
| **RFP → Idea Slate** (G1-G2) | 3-5 scouts + pre-award | Mostly Sonnet | ~10,000 | **$0.15–$0.30** |
| **Proposal Draft** (G3) | 8-10 agents | Sonnet + 2 Opus | ~20,000 | **$0.40–$0.80** |
| **Full Pre-Award** (G1-G3) | 10-15 agents | Sonnet + 3 Opus | ~35,000 | **$0.70–$1.50** |
| **Development Cycle** (G4) | 4-6 labs + exec + verify | Sonnet + 2 Opus | ~25,000 | **$0.50–$1.00** |
| **Report Writing** (G5-G6) | 2-3 reporting + support | Sonnet + 1 Opus | ~15,000 | **$0.30–$0.60** |
| **Full Lifecycle** (G1-G6) | 15-25 agents across phases | Mixed | ~75,000 | **$1.50–$3.50** |

**Key insight:** A full research project from RFP to final report costs roughly **$1.50 to $3.50** in Claude API tokens. This is remarkably cheap for what it produces.

### The Hidden Costs

| Cost Item | Amount | Who Pays |
|---|---|---|
| **Claude API** | $1.50–$3.50 per full project | User (researcher/university) |
| **Human rater time** (for studies) | $800–$1,500 per study | Institution (if running evaluations) |
| **Server infrastructure** (if self-hosted) | $50–$200/month | Institution |
| **Developer time** (setup, debugging) | 2–8 hours initially | Researcher |
| **Human gate time** | 30 min–2 hours per gate | PI (the real cost) |

The **real cost of Cambium is not the API tokens. It is the PI's time** at the 8 gates. A project that takes 2 hours of PI attention spread over a week is the actual economic unit.

### Missing:
- ❌ **No open-source model routing** — README says "Capable open models handle the routine bulk" but this is not shipped. Every agent call meters Claude tokens.
- ❌ **No cost prediction before running** — The user cannot see "this will cost $2.30" before clicking go.
- ❌ **No budget enforcement** — The institution profile can set `per_project_cap_usd: 0` and `require_human_approval_above_usd: 100`, but these are not enforced by `cambium_run.py`.
- ❌ **No cost alerts** — No notification when a project exceeds $10, $50, or the institution cap.
- ❌ **No cost optimization** — No prompt compression, no result caching, no duplicate query detection.

---

## 3. Cost Control & Budgeting

### What Exists

**Institution profile budget fields:**
```yaml
# governance/institution/PROFILE.example.yml
budget:
  per_project_cap_usd: 0          # 0 = must be set before any run
  monthly_cap_usd: 0
  require_human_approval_above_usd: 100
```

**Cost telemetry in CSV:** `agent_outputs/cost_log.csv` tracks per-run, per-phase, per-agent costs.

**Enforcement study budget transparency:** `BUDGET.md` publishes exact costs ($3–$13 model compute, $800–$1,500 rater time).

### What's Broken

**Budget fields are advisory, not enforced.** The `institution_profile.py` validator checks that the profile is well-formed, but `cambium_run.py` does not:
- Check `per_project_cap_usd` before starting a run
- Check `monthly_cap_usd` against accumulated spending
- Check `require_human_approval_above_usd` before exceeding the threshold
- Halt a run that would exceed the budget

The `budget` section in `PROFILE.example.yml` is a **policy document**, not a **runtime guardrail**. A run could burn through $500 in API tokens with no warning.

**No cost prediction:** Before running, the user sees:
```
mode: LIVE  |  provider: anthropic  |  max concurrent sessions: 5
```

But not:
```
Estimated cost: $2.30 (15 agents, ~35K tokens, 3 Opus + 12 Sonnet)
Budget remaining: $47.70 of $50 monthly cap
```

### Missing:
- ❌ Budget enforcement in `cambium_run.py`
- ❌ Cost prediction before run
- ❌ Monthly / weekly / daily spend tracking
- ❌ Cost alerts (email, Slack, dashboard)
- ❌ Automatic model downgrade when approaching budget cap
- ❌ Cost per deliverable report ("This proposal cost $1.85 to produce")

---

## 4. Latency per Agent Call

### What Exists

**Per-agent wall-clock tracking:**
```python
# tools/cambium_run.py line 140
txt, usage, wall = call_model(model, spec, "TASK: %s\nDo your job per your spec. Be concise." % task, key)
```

`wall` is the time in seconds for each API call. This is logged to `cost_log.csv`.

**API timeout:** 120 seconds (`urllib.request.urlopen(req, timeout=120)`)

**Pace enforcement:** `pace_check.py` enforces a 30-minute minimum between consecutive decision gates — this is a governance feature, not a performance optimization.

### What's Missing

**No latency histograms or percentiles.** The system logs wall-clock time but does not:
- Compute p50, p95, p99 latency
- Identify slow agents (which agent is consistently >60s?)
- Alert on latency spikes
- Optimize slow prompts
- Cache slow queries

**No async/await for API calls.** `cambium_run.py` uses blocking `urllib.request`:
```python
# tools/cambium_run.py lines 60-68
req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=body,
        headers={"x-api-key": key, "anthropic-version":"2023-06-01", "content-type":"application/json"})
with urllib.request.urlopen(req, timeout=120) as r:
    d = json.loads(r.read())
```

This is **synchronous I/O**. While concurrent agents run in a `ThreadPoolExecutor`, each individual API call blocks the thread. There is no:
- `asyncio` / `aiohttp` for non-blocking API calls
- Connection pooling (`requests.Session`, `urllib3.PoolManager`)
- HTTP/2 multiplexing
- Retry with exponential backoff (only a single 120s timeout)

**No latency SLA.** The user has no idea how long a phase will take. A 5-agent parallel phase with 60s average latency = 60s wall-clock (parallel), but with retry storms or API degradation it could take 10+ minutes.

### Missing:
- ❌ Latency histograms (p50, p95, p99)
- ❌ Async HTTP client (aiohttp, httpx)
- ❌ Connection pooling
- ❌ Retry with exponential backoff and jitter
- ❌ Circuit breaker pattern for API degradation
- ❌ Latency SLA alerts
- ❌ Prompt optimization for speed (shorter prompts = faster responses)
- ❌ Streaming responses for early feedback

---

## 5. Throughput (Concurrent Users)

### What Exists

**ThreadPoolExecutor for agent concurrency:**
```python
# tools/cambium_run.py lines 166-168
with cf.ThreadPoolExecutor(max_workers=maxc) as ex:
    for name, model, st in ex.map(run_one, ags):
```

Default `maxc = 5` (configurable via `--max N`). This means up to 5 agents can call the API simultaneously within a single phase.

**Web server:** FastAPI with `asyncio` — technically capable of handling multiple concurrent WebSocket connections, but the `RUNS` dictionary is in-memory and unbounded.

### What's Broken

**Single-user architecture.** Cambium is designed for "a single Claude project with one Director (PI)." The entire system assumes:
- One `config.yml` per machine
- One `RUNS` dictionary in the web server
- One `agent_outputs/` directory
- One `governance/GATES.md` ledger

**There is no multi-user support.** If 100 students in a class all run Cambium simultaneously:
- Each needs their own `config.yml` (or they overwrite each other's)
- Each needs their own `agent_outputs/` directory (or they overwrite each other's)
- Each needs their own `governance/GATES.md` (or they overwrite each other's)
- The web server's `RUNS` dictionary grows unbounded (memory leak)

**No database.** All state is in flat files (CSV, JSON, Markdown). Concurrent writes to the same file will corrupt it. There is no:
- Database (PostgreSQL, SQLite, MongoDB)
- Message queue (Redis, RabbitMQ, Kafka)
- Task queue (Celery, RQ, Dramatiq)
- Session store (Redis, memcached)
- Load balancer

**No horizontal scaling.** The web server runs on a single process (`uvicorn web.server.app:app`). There is no:
- Multi-process worker pool
- Kubernetes deployment with auto-scaling
- Serverless (AWS Lambda, Google Cloud Functions)
- Container orchestration (no `docker-compose.yml`, no Helm chart)

### The Math: What 100 Concurrent Users Would Look Like

| Metric | Current | Required for 100 Users |
|---|---|---|
| **Max concurrent API calls** | 5 | 500+ |
| **State storage** | Flat files in `agent_outputs/` | PostgreSQL + Redis |
| **User isolation** | None (shared directory) | Multi-tenant DB with row-level security |
| **Session management** | In-memory `RUNS` dict | Redis session store |
| **Queueing** | None | Celery + Redis for background jobs |
| **Load balancing** | None | nginx + multiple uvicorn workers |
| **Auto-scaling** | None | Kubernetes HPA |

### Missing:
- ❌ Database layer (PostgreSQL, SQLite)
- ❌ Message queue (Redis, RabbitMQ)
- ❌ Task queue (Celery, RQ)
- ❌ Multi-tenancy (isolated projects per user)
- ❌ Session management (Redis, JWT)
- ❌ Load balancing (nginx, Traefik)
- ❌ Horizontal scaling (K8s, Docker Swarm)
- ❌ Auto-scaling (HPA, serverless)
- ❌ Resource quotas per user

---

## 6. Scalability

### What Exists

**Deterministic check registry:** `tools/deterministic_checks.py` — 10 of 16 checks are grounded (no model calls), which scales well because they are pure computation.

**Agent-as-a-Judge evaluation:** `tools/agent_eval.py` scores trajectories deterministically without API calls.

**Simulation mode:** `web/server/engine.py` runs in simulation by default (no API calls, no cost), which is infinitely scalable for demos.

### What's Broken

**No caching layer.** Every agent call is a fresh API call. There is no:
- Redis cache for repeated queries
- Memoization of deterministic checks
- Pre-computed agent responses for common tasks
- CDN for static assets
- Browser caching headers

**No connection pooling.** Each API call opens a new HTTPS connection to `api.anthropic.com`. With 100 users × 10 agents = 1,000 API calls, this creates 1,000 TCP handshakes + TLS negotiations. With connection pooling, it would be ~10 persistent connections.

**No database → no query optimization.** All state lookups are file system reads (O(n) glob operations). A project with 1,000 files in `agent_outputs/` becomes slow to scan.

**No async architecture.** The web server uses `asyncio` for WebSocket streaming but the backend (`cambium_run.py`) uses synchronous threads. The Orchestrator dispatches agents sequentially with blocking waits.

### Missing:
- ❌ Redis caching layer
- ❌ Connection pooling for API calls
- ❌ Database for state and queries
- ❌ Async/await throughout the backend
- ❌ CDN for frontend assets
- ❌ Static asset compression (gzip, Brotli)
- ❌ Lazy loading for agent specs
- ❌ Incremental state updates (only changed fields)

---

## 7. Memory & Resource Footprint

### What Exists

**Lightweight Python runtime:** The core system uses Python stdlib + PyYAML + FastAPI + Uvicorn. No heavy dependencies like PyTorch, TensorFlow, or large vector databases.

**No persistent memory usage:** Each run is stateless after completion (state is written to disk).

### What's Broken

**No memory profiling.** The system has no idea how much RAM it uses. There is no:
- `memory_profiler` integration
- `tracemalloc` for leak detection
- Kubernetes resource limits
- Docker memory constraints
- OOM (out-of-memory) handling

**No resource limits.** A single run could:
- Spawn 100 concurrent agents (if `--max 100` is passed)
- Each agent downloads large files (if the scout fetches a 100MB PDF)
- The `ThreadPoolExecutor` could exhaust the thread pool
- The `RUNS` dictionary grows unbounded (no eviction policy)

**No garbage collection tuning.** Python's default GC is not tuned for long-running processes. The web server could accumulate memory leaks over days.

### Missing:
- ❌ Memory profiling and monitoring
- ❌ Resource limits (CPU, RAM, disk, network)
- ❌ OOM handling and graceful degradation
- ❌ GC tuning for long-running processes
- ❌ Memory leak detection
- ❌ Disk space monitoring (logs, agent outputs, ledgers grow indefinitely)

---

## 8. Cold Start Time

### What Exists

**Fast Python startup:** `python3 tools/cambium_run.py` starts in <1 second.

**Fast web server startup:** `uvicorn web.server.app:app` starts in ~2 seconds.

**No heavy imports:** The core tools avoid importing heavy libraries at startup.

### What's Broken

**First API call is cold.** There is no:
- Warm pool of API connections
- Pre-loaded model context
- Cached agent specs in memory
- Prefetching of common queries

**No warm-start for the web server:** The first WebSocket connection triggers the simulation, which is instant, but a live run requires the full agent roster load and model resolution.

**No serverless optimization:** If deployed to AWS Lambda or Google Cloud Functions, the cold start would include:
- Python runtime initialization (~200ms)
- FastAPI import (~500ms)
- Agent roster loading (~100ms)
- First API call connection setup (~1-2s)
- Total: **2-4 seconds** per cold start

This is acceptable for a web app but poor for a serverless API.

### Missing:
- ❌ Connection warm pool
- ❌ Pre-loaded agent cache
- ❌ Warm-start for serverless deployments
- ❌ Keep-alive for API connections
- ❌ Lazy loading for infrequently used agents

---

## 9. Infrastructure Economics

### What Exists

**Self-hosted, no SaaS:** No subscription fees, no per-user pricing. The only cost is API tokens and (optionally) server hosting.

**Minimal server requirements:** The web server runs on a single CPU with <512MB RAM.

**Docker support:** A basic `Dockerfile` exists.

### What's Broken

**No database → no multi-tenancy → no economies of scale.** Each user needs a full instance. A university with 1,000 students cannot run a single shared Cambium instance. They need either:
- 1,000 individual installations (each with their own `config.yml`, `agent_outputs/`, `governance/`)
- Or a multi-tenant platform that does not exist yet

**No CDN.** The web frontend (`web/frontend/index.html` = 167 lines, ~12KB) is tiny, but:
- No CDN for global distribution
- No edge caching for API responses
- No geographic load balancing
- All traffic goes to the origin server

**No auto-scaling.** If a professor assigns Cambium to 80 students and they all start a run at 9:00 AM:
- The web server handles it with asyncio (maybe)
- The backend (`cambium_run.py`) queues up in a single thread pool
- API rate limits from Anthropic kick in (429 errors)
- No retry queue, no graceful degradation
- Students see timeouts or errors

**No infrastructure-as-code.** There is no:
- Terraform / CloudFormation / Pulumi
- Kubernetes manifests
- Helm charts
- Docker Compose
- GitHub Actions for deployment

### Missing:
- ❌ CDN (Cloudflare, AWS CloudFront, Fastly)
- ❌ Auto-scaling (K8s HPA, AWS Auto Scaling)
- ❌ Infrastructure-as-code (Terraform, Pulumi)
- ❌ Multi-tenancy platform
- ❌ Geographic distribution
- ❌ Edge computing (Cloudflare Workers, AWS Lambda@Edge)
- ❌ Monitoring (Prometheus, Grafana, Datadog)
- ❌ Alerting (PagerDuty, PagerTree, Slack)

---

## 10. Performance Benchmarks

### What Exists

**Deterministic evals:** `tools/agent_eval.py` scores trajectories without API calls.

**Self-grading:** `tools/doctor.py --grade` gives an A-F score.

**Dashboard:** `assets/benchmark_dashboard.html` shows tests passing, doctor grade, enforcement gauntlet status, and A/B study results.

### What's Broken

**No performance benchmarks.** The dashboard shows governance metrics, not performance metrics:
- ❌ No "time to first gate" benchmark
- ❌ No "time to completed proposal" benchmark
- ❌ No "tokens per deliverable" benchmark
- ❌ No "cost per gate" benchmark
- ❌ No latency percentile tracking
- ❌ No throughput benchmark (requests per second)
- ❌ No load test results (how many concurrent users?)
- ❌ No stress test results (what breaks first?)

**No performance regression CI.** The GitHub Actions workflow validates agent frontmatter and governance but does not:
- Run performance benchmarks
- Compare PR branch vs. main branch latency
- Flag performance regressions
- Test under load

### Missing:
- ❌ Performance benchmark suite (locust, k6, Apache Bench)
- ❌ Load testing (100, 1,000, 10,000 concurrent users)
- ❌ Stress testing (what breaks at 10× normal load?)
- ❌ Performance regression CI
- ❌ Latency tracking over time
- ❌ Cost tracking over time
- ❌ Token efficiency metrics (tokens per unit of work)

---

## 11. The Honest Cost Economics

### Cambium's Cost Advantage

| Competitor | Cost Model | Cambium Comparison |
|---|---|---|
| **Elicit** | $49/month Pro, $169/month Scale, Enterprise custom | Cambium is free (MIT) + API tokens. Elicit is cheaper for heavy users. |
| **Sakana AI Scientist** | ~$15 per paper (autonomous, GPU) | Cambium is cheaper per project but requires human time. |
| **Google Co-Scientist** | Cloud service (unknown pricing, likely Enterprise) | Cambium is self-hosted, no lock-in, but less capable. |
| **OpenAI o3** | $1,000+ per hard task | Cambium uses Claude ($0.50–$3.50 per project) — vastly cheaper. |
| **Claude Code** | $20/month Pro + API costs | Cambium is a layer on top of Claude Code, not a replacement. |
| **Paperguide** | Free tier + paid tiers | Comparable to Cambium's free tier but with more features. |

### Cambium's Cost Disadvantage

| Factor | Impact |
|---|---|
| **Human PI time** | 30 min–2 hours per gate × 8 gates = 4–16 hours of PI time per project. At $100/hr (faculty rate), that's **$400–$1,600** in labor cost. |
| **No caching** | Repeated similar queries cost full price every time. |
| **No open-source models** | Every call costs Claude API tokens. With 100 students, this adds up fast. |
| **No multi-tenancy** | Each user needs a full instance. IT overhead per user is high. |
| **Infrastructure** | Self-hosting requires a server, DNS, SSL, backups — $50–$500/month. |

### The Real Economics

For a **solo researcher** running 10 projects/month:
- API cost: $15–$35/month
- Infrastructure: $0 (laptop)
- Total: **$15–$35/month** — excellent value

For a **university with 100 students** each running 2 projects/month:
- API cost: 100 × 2 × $2.50 = **$500/month**
- Infrastructure: 10 instances × $50 = **$500/month** (no multi-tenancy)
- IT overhead: 20 hours/month × $75 = **$1,500/month**
- Total: **$2,500/month** — requires institutional budget

For a **university with 1,000 students**:
- API cost: 1,000 × 2 × $2.50 = **$5,000/month**
- Infrastructure: 100 instances × $50 = **$5,000/month**
- IT overhead: 200 hours/month × $75 = **$15,000/month**
- Total: **$25,000/month** — requires enterprise platform (which Cambium is not yet)

---

## 12. Actionable Roadmap for Performance & Cost

### Phase 1: Cost Control (Weeks 1–2) — Critical for Institutional Adoption

| Step | Action | Impact |
|---|---|---|
| 1.1 | **Budget enforcement in `cambium_run.py`** — halt if `per_project_cap_usd` or `monthly_cap_usd` exceeded | Prevents runaway spending |
| 1.2 | **Pre-run cost prediction** — estimate tokens × price before execution | User informed consent |
| 1.3 | **Cost alerts** — notify user at 50%, 80%, 100% of budget | Prevents surprises |
| 1.4 | **Cost per deliverable report** — "This proposal cost $1.85" | Transparency |

### Phase 2: Performance (Weeks 3–4) — Critical for UX

| Step | Action | Impact |
|---|---|---|
| 2.1 | **Async HTTP client** — Replace `urllib` with `httpx` + `asyncio` | Faster API calls, better concurrency |
| 2.2 | **Connection pooling** — `httpx.AsyncClient` with persistent connections | Reduces TCP/TLS overhead |
| 2.3 | **Retry with exponential backoff** — Handle 429s, 503s gracefully | Reliability |
| 2.4 | **Latency histograms** — Track p50, p95, p99 per agent | Identify bottlenecks |
| 2.5 | **Prompt caching** — Cache stable context (charter, specs) per EFFICIENCY.md | Cuts repeated token costs |

### Phase 3: Scalability (Weeks 5–8) — Critical for Universities

| Step | Action | Impact |
|---|---|---|
| 3.1 | **SQLite database** — Replace flat files with SQLite for state, ledgers, gate records | Enables concurrent access |
| 3.2 | **Redis cache** — Cache agent specs, common queries, gate states | Reduces API calls, faster responses |
| 3.3 | **Task queue (Celery + Redis)** — Background agent execution, queue management | Handles 1,000+ concurrent users |
| 3.4 | **Multi-tenancy** — Isolated projects per user with row-level security | One server, many users |
| 3.5 | **Load balancer** — nginx with multiple uvicorn workers | Horizontal scaling |
| 3.6 | **Docker Compose** — One-command deployment with DB + Redis + app | Easy ops |

### Phase 4: Open-Source Models (Weeks 9–12) — Cost Reduction

| Step | Action | Impact |
|---|---|---|
| 4.1 | **Open-source model integration** — Route bulk tasks (formatting, digests) to local models (Llama, Mistral, DeepSeek) | 80% cost reduction |
| 4.2 | **Local model server** — vLLM or Ollama for on-premise inference | Zero token cost for bulk work |
| 4.3 | **Hybrid routing** — Frontier (Claude) for gates, open-source for everything else | Optimal cost/quality |
| 4.4 | **GPU scheduling** — Kubernetes with GPU nodes for local models | Scalable local inference |

### Phase 5: Benchmarking (Ongoing) — Accountability

| Step | Action | Impact |
|---|---|---|
| 5.1 | **Performance benchmark suite** — Time-to-gate, time-to-proposal, tokens-per-deliverable | Measure improvement |
| 5.2 | **Load testing** — k6 or locust with 100, 1,000, 10,000 concurrent users | Find bottlenecks |
| 5.3 | **Performance regression CI** — Flag PRs that slow down the system | Protect speed |
| 5.4 | **Cost dashboard** — Real-time spend per user, per project, per department | Budget visibility |

---

## 13. Final Verdict

### Performance & Cost Grades

| Dimension | Grade | Status |
|---|---|---|
| Token Cost per Project | B+ | Cheap, honest, well-tracked |
| Cost Control & Budgeting | C | Tracks but doesn't enforce |
| Latency per Agent Call | C | No async, no pooling, no histograms |
| Throughput (Concurrent Users) | D | Single-user architecture |
| Scalability | D | No caching, no DB, no queueing |
| Memory & Resource Footprint | C | Lightweight but unmonitored |
| Cold Start Time | B | Fast Python, slow first API call |
| Infrastructure Economics | D | No CDN, no auto-scaling, no multi-tenancy |
| Cost Transparency | A | Excellent per-agent logging |
| Performance Benchmarks | D | None |

**Overall Performance & Cost Grade: C**

### What a University CFO Will Ask:

> "If we deploy this to 500 students, what does it cost per month? Can we cap spending? Does it run on our existing infrastructure? Do we need a dedicated DevOps team?"

**Cambium's answers today:**
- "Roughly $5,000/month in API tokens, plus $5,000 in infrastructure, plus $15,000 in IT overhead."
- "No, you cannot cap spending automatically."
- "It runs on a single Docker container with no database."
- "You will need someone to manually manage 100+ instances."

### The Honest Bottom Line:

**Cambium is a Ferrari that runs on premium gas and has no gas gauge.** It is cheap and fast for a single driver, but you cannot put 1,000 drivers in the same car. To scale to institutional use, Cambium needs a **database, a cache, a task queue, multi-tenancy, and open-source model routing** — all of which are missing today. The cost model is honest, but the cost controls are missing. The performance is acceptable for one user, but the scalability is nonexistent for a thousand.

**Performance is not a feature you add when you have users. It is the architecture you build before you have them.**

---

*Performance evaluation completed 2026-06-28. Based on Cambium v1.9.3. Per-project cost: $1.50–$3.50. Per-100-students cost: ~$2,500/month. No caching, no database, no queueing, no multi-tenancy, no performance benchmarks.*
