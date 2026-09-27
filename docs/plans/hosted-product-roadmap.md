# AgentEase product roadmap (approved)

**Status:** Approved 2026-09-27  
**North star:** AgentEase Cloud — hosted control plane for policy, audit, observability, and workflow governance, with the Python SDK as the default **data plane** (runs in the customer environment).

**Canonical copy:** This file in the repository. Future agents should read this before large product or architecture changes.

---

## Current baseline (0.2.0)

- **Pipeline:** raw text → local regex scrubber → provider → schema validate/repair → typed result.
- **Templates:** support triage (flagship), lead qualification, document classification.
- **Architecture:** `WorkflowSpec` / `WorkflowAgent` in `agentease/templates/base.py` — new workflows are schema + instruction, not a new pipeline.
- **Providers:** OpenAI release-certified; other LiteLLM providers best-effort.
- **Integration:** JSONL batch triage example; offline deterministic fixtures for all three workflows.
- **Telemetry today:** in-memory `MetricsRecorder` only; `GuardrailReport` is privacy-safe (PII types, char counts, repair count — no raw input).
- **Explicit non-goals in 0.2.0:** hosted dashboard, remote telemetry, audit logs, policy management, RAG/OCR, Node SDK, Presidio/ML NER, streaming, enterprise deploy.

**0.3 signal in code:** Remove compatibility aliases (`client.leads`, `client.docs`, `DocClassificationResult`) through the 0.3 release line.

---

## Open SDK vs hosted product

| Concern | Open SDK | Hosted (monetize) |
|--------|----------|-------------------|
| Scrubbing & schema pipeline | Yes | Policy *definitions* in cloud; scrub execution stays client-side by default |
| Provider keys | Customer BYOK | Optional AgentEase gateway or BYOK + proxy |
| Run metadata | `MetricsRecorder`, `GuardrailReport` | Durable runs, search, retention, export |
| Policy | Local `PiiScrubber` | Versioned org policies, publish workflow |
| Workflows | Built-in + `WorkflowSpec` | Registered templates, prompt/schema versions |
| Identity | N/A | Orgs, users, RBAC, API keys |
| Compliance narrative | SECURITY.md | Audit log, retention, DPA, residency |

**Principle:** SDK remains fully useful offline with no AgentEase account. Cloud is opt-in.

---

## Target architecture

```text
┌──────────────── Customer environment ─────────────────┐
│  App → AgentEase SDK                                 │
│         ├─ local scrub (default)                     │
│         ├─ optional: fetch policy snapshot (cached)  │
│         └─ LLM: direct BYOK OR via AgentEase gateway │
└──────────────────────────┬──────────────────────────┘
                           │ HTTPS (metadata + optional gateway)
┌──────────────────────────▼──────────────────────────┐
│  AgentEase Cloud                                       │
│  Auth · Orgs · Policies · Workflow registry · Runs DB  │
│  Dashboard · Audit export · Alerts                     │
└───────────────────────────────────────────────────────┘
```

### Default privacy posture (v1)

- **Do not ingest raw workflow text** unless customer opts into cloud processing.
- Upload **privacy-safe run records:** workflow name, schema version, success, duration, repair count, detected PII *types*, `run_id`, optional external id (e.g. ticket id).
- Scrubbing stays **local by default** (matches README/SECURITY; sales feature).

### Optional v2

- AgentEase **LLM gateway** (sanitized prompts only) for unified billing and key rotation.

---

## SDK work (hosted enablers — backward compatible)

Build in OSS before or in parallel with cloud MVP:

1. **Stable `run_id`** — UUID per `run_with_report()`; include in metrics metadata and cloud export.
2. **HTTP `MetricsRecorder`** — POST batched events to `AGENTEASE_API_URL`; fail-open (same spirit as `record_non_blocking`).
3. **Policy snapshot type** — Frozen config: scrubber extras, `max_repair_attempts`, model allowlist, workflow version; fetch from cloud, cache with TTL.
4. **Env extension** — `AGENTEASE_API_KEY`, `AGENTEASE_ENV`, `AGENTEASE_PROJECT_ID` (+ document in `.env.example`).
5. **Workflow versioning** — Optional `version` on `WorkflowSpec`; cloud stores `(name, version) → instruction + JSON schema`.

**Do not** put dashboard UI or auth inside the PyPI package. Prefer separate `agentease-cloud` repo/service early.

---

## Hosted MVP (v1 cloud)

**Must have**

- Sign up / org / project
- API keys for telemetry (gateway later)
- Runs list: time, workflow, success, latency, repairs, PII types, SDK version
- Policy v0: org defaults (max repair, model allowlist, extra regex JSON)
- Audit export (CSV/JSON), ~90 day retention
- Dashboard: volume, failure rate, repair rate, by workflow

**Out of MVP**

- RAG, OCR, Presidio-as-a-service, Node SDK, full prompt logging, multi-region dedicated cells

**GTM wedge:** support triage + JSONL batch (`examples/batch_triage_jsonl.py`).

---

## Phased delivery

### Phase A — Foundation (weeks 1–6)

- 0.3 compat cleanup (stable public API)
- `run_id`, workflow `version`, HTTP metrics adapter (env-gated)
- OpenAPI sketch: `POST /v1/runs/events`, `GET /v1/policies/{project}`
- This roadmap doc maintained in repo

**Exit:** SDK emits cloud-shaped events to stub/mock.

### Phase B — Cloud MVP (weeks 7–14)

- Auth, Postgres (runs + policies), minimal dashboard
- Ingest SDK events; policy fetch + SDK cache

**Exit:** One design partner: local scrub + cloud audit in production.

### Phase C — Gateway & governance (weeks 15–24)

- Optional sanitized LLM proxy, metering, rate limits
- Policy draft → publish; alerts on validation/repair spikes

**Exit:** Paid tier: audit + policy + optional gateway.

### Phase D — Enterprise (revenue-driven)

- SSO, SCIM, extended retention, immutable audit export (e.g. customer S3)
- Private VPC template after multi-tenant MVP is solid

---

## 90-day critical path

| Month | Deliverable |
|-------|-------------|
| 1 | `run_id`, event schema, HTTP exporter, policy snapshot types, **0.3** release |
| 2 | Cloud ingest + API keys + runs API; dogfood triage |
| 3 | Minimal dashboard + policy publish + one pilot (triage/batch) |

---

## Sequencing notes (hosted lens)

- **Custom workflows docs** — Yes; cloud registers customer `WorkflowSpec` versions.
- **Batch for all templates** — Yes; cloud correlates batch `run_id`s.
- **Local metrics summary** — Dev convenience; cloud dashboard is primary in prod.
- **Presidio / RAG** — Defer past MVP.
- **Second provider certification** — Prioritize if gateway is on near-term roadmap (server-side matrix).

---

## Early business / trust decisions

1. **BYOK + metadata-only first** vs **gateway-first** (trust vs monetization speed).
2. **Data residency** — Pick primary region for Postgres from day one.
3. **Open core** — SDK MIT; cloud proprietary; no required phone-home in OSS.
4. **Pricing** — Runs/month + retention + seats; gateway adds usage fee or pass-through.

---

## Risks

- Scope creep into RAG or “full LLM platform UI” — MVP is **runs + policy + audit** only.
- Logging raw text for debugging — undermines security story; metadata-only unless explicit opt-in.
- Monorepo coupling — Keep separate deploy pipeline for PyPI vs cloud.

---

## Next execution artifacts (when implementing)

1. v1 run event JSON schema (align with `MetricEvent` + `GuardrailReport`)
2. OpenAPI for ingest + policy
3. `agentease-cloud` repo layout (API + worker + dashboard)
