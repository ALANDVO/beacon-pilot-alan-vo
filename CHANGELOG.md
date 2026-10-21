# Changelog

## 1.0.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-10-21

### Added
- FastAPI backend with memory CRUD API (create, list, get, update, delete)
- SQLite persistence with SQLAlchemy async ORM
- Memory unit model with document_id, content, tags, metadata, observation_scopes
- Consolidation engine with similarity-based deduplication (difflib.SequenceMatcher)
- Consolidation batch API (create, status, run with report)
- Audit logging for all mutations (create, update, delete)
- Pagination and filtering (document_id, tag, is_consolidated, search)
- React + TypeScript + Vite frontend
- Memory list page with table, pagination, filters, create/edit/delete dialogs
- Memory detail page with full content, metadata, tags, scopes
- Consolidation page with batch creation, execution, and report viewing
- Responsive layout with sidebar navigation
- Loading, error, and empty states
- Typed API client derived from backend schemas
- OIDC/PKCE authentication infrastructure (Keycloak realm export)
- Dockerfiles for backend (Python 3.12) and frontend (Node 24 + nginx)
- Docker Compose with backend, frontend, Keycloak profiles
- GitHub Actions CI workflow (backend tests, frontend tests, Docker builds)
- Health checks for all services
- Comprehensive test suites (backend: 15 tests, frontend: 3 tests)

### Security
- Parameterized SQL queries via SQLAlchemy
- Pydantic validation on all API endpoints
- CORS configured for development origins
- No hardcoded secrets; all credentials via environment variables
- OIDC-only authentication with PKCE for SPA

### Documentation
- README with architecture diagram, API reference, quick start
- Portfolio.json with schema_version, workflows, auth, providers
- MIT LICENSE
- .env.example with all configuration options