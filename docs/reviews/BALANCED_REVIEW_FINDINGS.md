# Balanced Review Findings

This report captures the validated findings from the remediation pass and the implemented fix intent.

## Critical

- Frontend/backend user-session contract drift:
  - Frontend hooks still carried user-switch semantics while backend is PoC-first-user.
  - Fix intent: remove unsupported switching hooks and keep a single-user-safe query contract.

- Processing pipeline partial outcome opacity:
  - Legacy processing loop could continue after per-article failures without explicit failed IDs.
  - Fix intent: isolate failed articles, rollback on exception, and return explicit `failed_article_ids`.

## High

- Error normalization inconsistency in API client:
  - Timeout/network/validation failures were not normalized in one place for UI handling.
  - Fix intent: centralize Axios error normalization and preserve actionable user messages.

- Mutable preference/onboarding payload guardrails:
  - Route handlers accepted effectively empty onboarding/preference payloads after normalization.
  - Fix intent: enforce non-empty name/interests/sources and reject empty preference patch payloads.

## Medium (Quick Wins)

- Noisy preference writes from rapid slider interaction:
  - Daily digest limit slider emitted many update requests.
  - Fix intent: debounce high-frequency slider updates.

- Missing explicit fallback states in user-facing pages:
  - Analytics and preferences screens lacked explicit error fallback rendering.
  - Fix intent: add clear loading/error fallback UI where missing.

## Documentation Corrections

- API/docs contract drift:
  - Pagination docs used `skip/limit` while API uses `page/page_size`.
  - Pipeline docs and examples were partially inconsistent with active `routes_v2`.
  - Fix intent: align endpoint references, request params, and sample response fields.

- Developer guide path/config drift:
  - Type file paths and frontend directory names had stale references.
  - Fix intent: update paths and API client examples to match current project layout.
