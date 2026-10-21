# Product development plan

Each round completes one feature or repair. Future items are planned, not implemented claims.

## Current round

core-api-skeleton

## Roadmap

### core-api-skeleton — Core FastAPI skeleton with health check and basic memory CRUD

Status: in_progress

Acceptance:
- FastAPI app starts and serves /health endpoint
- SQLite persistence with memory units table
- POST /memories creates a memory unit
- GET /memories lists memory units with pagination
- GET /memories/{id} retrieves a single memory unit
- DELETE /memories/{id} deletes a memory unit
- Backend tests pass for CRUD operations

Implementation: `backend/app/main.py`, `backend/app/api/memories.py`, `backend/app/models/memory.py`, `backend/app/core/database.py`, `backend/app/core/config.py`, `backend/requirements.txt`, `backend/tests/test_memories.py`

Tests: `backend/tests/test_memories.py`

### memory-extraction-engine — Deterministic memory extraction engine (offline core)

Status: planned

Acceptance:
- Extract structured facts from conversation text without LLM
- Rule-based entity/relationship extraction
- Configurable extraction rules
- Unit tests for extraction logic

Implementation: `backend/app/services/extraction.py`, `backend/app/services/rules.py`, `backend/tests/test_extraction.py`

Tests: `backend/tests/test_extraction.py`

### consolidation-workflow — Memory consolidation workflow with deduplication

Status: planned

Acceptance:
- POST /consolidate triggers consolidation job
- Deduplicates similar memory units
- Merges related facts
- Returns consolidation report

Implementation: `backend/app/services/consolidation.py`, `backend/app/api/consolidation.py`, `backend/tests/test_consolidation.py`

Tests: `backend/tests/test_consolidation.py`

### frontend-skeleton — React + TypeScript + Vite frontend with memory dashboard

Status: planned

Acceptance:
- Vite dev server runs
- TypeScript compiles without errors
- Memory list page with create/edit/delete
- Loading/error/empty states
- API client with typed endpoints

Implementation: `frontend/package.json`, `frontend/src/App.tsx`, `frontend/src/components/MemoryList.tsx`, `frontend/src/components/MemoryForm.tsx`, `frontend/src/api/client.ts`, `frontend/src/types/api.ts`

Tests: `frontend/src/__tests__/MemoryList.test.tsx`

### oidc-auth — OIDC Keycloak authentication with PKCE

Status: planned

Acceptance:
- Login redirects to Keycloak
- Callback exchanges code for tokens
- Protected API endpoints require valid token
- Logout clears session

Implementation: `backend/app/core/auth.py`, `backend/app/api/auth.py`, `frontend/src/components/Login.tsx`, `frontend/src/auth/provider.tsx`

Tests: `backend/tests/test_auth.py`

### llm-adapters — LLM provider adapters (OpenAI-compatible, Anthropic, Gemini, Ollama)

Status: planned

Acceptance:
- Configurable provider via env vars
- OpenAI-compatible adapter works
- Anthropic messages adapter works
- Gemini generateContent adapter works
- Ollama adapter works
- Redacted error handling

Implementation: `backend/app/services/llm/adapters.py`, `backend/app/services/llm/base.py`, `backend/tests/test_llm_adapters.py`

Tests: `backend/tests/test_llm_adapters.py`

### docker-ci — Dockerfiles, compose.yaml, and CI workflow

Status: planned

Acceptance:
- Backend Dockerfile builds and runs
- Frontend Dockerfile builds and runs
- compose.yaml includes Keycloak and volumes
- CI runs backend/frontend tests and builds
- Healthchecks configured

Implementation: `Dockerfile.backend`, `Dockerfile.frontend`, `compose.yaml`, `.github/workflows/ci.yml`, `.env.example`

### docs-portfolio — README, portfolio.json, LICENSE, CHANGELOG

Status: planned

Acceptance:
- README with install/run/test steps
- Mermaid architecture diagram
- API endpoint reference
- portfolio.json at root
- MIT LICENSE
- CHANGELOG.md

Implementation: `README.md`, `portfolio.json`, `LICENSE`, `CHANGELOG.md`, `pyproject.toml`

