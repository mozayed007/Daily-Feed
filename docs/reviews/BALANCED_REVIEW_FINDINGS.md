# Balanced Review Findings

This report captures the validated findings from the remediation pass and the implemented fix intent.

**Legend:** [x] = Verified fixed | [ ] = Pending | [-] = Not applicable / Won't fix

---

## Critical

- [x] **Frontend/backend user-session contract drift**
  - Frontend hooks still carried user-switch semantics while backend is PoC-first-user.
  - Fix: removed unsupported switching hooks; `useUser.ts` now uses a single-user-safe query contract against `/users/me`.

- [x] **Processing pipeline partial outcome opacity**
  - Legacy processing loop could continue after per-article failures without explicit failed IDs.
  - Fix: pydantic-graph `ArticleProcessingGraph` isolates failed articles per-step; `failed_ids` are collected in `PipelineState` and returned in the graph output.

## High

- [x] **Error normalization inconsistency in API client**
  - Timeout/network/validation failures were not normalized in one place for UI handling.
  - Fix: `frontend/src/lib/api.ts` centralizes Axios error normalization via `normalizeApiErrorMessage()` and handles `ECONNABORTED` / no-response cases with actionable messages.

- [x] **Mutable preference/onboarding payload guardrails**
  - Route handlers accepted effectively empty onboarding/preference payloads after normalization.
  - Fix: onboarding and preference endpoints now enforce non-empty `name`/`interests`/`sources` and reject empty preference patch payloads at the Pydantic model layer.

## Medium (Quick Wins)

- [x] **Noisy preference writes from rapid slider interaction**
  - Daily digest limit slider emitted many update requests.
  - Fix: debounced high-frequency slider updates in `Preferences.tsx`.

- [x] **Missing explicit fallback states in user-facing pages**
  - Analytics and preferences screens lacked explicit error fallback rendering.
  - Fix: `EmptyState` and `ErrorDisplay` components applied across `Home`, `History`, `Stats`, `Preferences`, and `Scheduler` pages.

## Documentation Corrections

- [x] **API/docs contract drift**
  - Pagination docs used `skip/limit` while API uses `page/page_size`.
  - Fix: `docs/api/API.md` and `docs/api/API_TYPES.ts` updated to `page`/`page_size`. Pipeline docs aligned with `routes_v2` endpoints.

- [x] **Developer guide path/config drift**
  - Type file paths and frontend directory names had stale references.
  - Fix: `docs/guides/FRONTEND_STARTER_GUIDE.md` updated to reflect actual project layout (removed references to non-existent `useDigest.ts`, `queryClient.ts`, `Digest.tsx`).

## Post-Fix Verification Notes

All critical and high findings have been verified against:
- `frontend/src/lib/api.ts` — error normalization logic
- `frontend/src/hooks/useUser.ts` — single-user query contract
- `backend/app/ai/graphs.py` — `PipelineState.failed_ids` collection
- `backend/app/api/user_routes.py` — payload validation guards
- `frontend/src/pages/Preferences.tsx` — debounced slider
- `frontend/src/components/EmptyState.tsx` — fallback usage across pages

Documentation corrections verified by cross-referencing `routes_v2.py` endpoints against `docs/api/API.md`.
