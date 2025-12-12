# GPROX Modernization Plan

The current code base delivers the right DNS automation features but relies on a monolithic WSGI module. To prepare the project for broader publication we should migrate to FastAPI, adopt Gunicorn with Uvicorn workers, and break the code into clearly defined packages.

---

## Objectives
- Provide a first-class ASGI application with FastAPI for maintainable routing and automatic docs.
- Enforce clear boundaries between API routes, domain logic, and Google Cloud integrations.
- Retain backwards-compatible behavior for `/v1/health`, `/v1/live`, `/v1/dns/add`, and `/v1/dns/remove`.
- Maintain current configuration semantics (YAML file, env overrides) while making them injectable.
- Enable easier unit/integration testing and dependency injection.

---

## Target Layout

```
app/
  core/
    config.py         # load/validate settings
    logging.py        # logging setup helpers
  services/
    dns_client.py     # wraps googleapiclient interactions
    dns_manager.py    # add/remove TXT orchestrations
    auth.py           # API key validation helpers
  api/
    models.py         # Pydantic request/response schemas
    deps.py           # FastAPI dependencies (config, services)
    routes/
      health.py
      dns.py
  main.py             # FastAPI app factory + router registration
```

This structure separates framework glue (FastAPI) from the DNS logic so we can test services independently and swap transports later if needed.

---

## Implementation Steps
1. **Configuration layer**
   - Create `Settings` Pydantic model that loads YAML on startup (respecting `GPROX_CONFIG_PATH`).
   - Expose dependency function that returns memoized settings for routes/services.

2. **Logging initialization**
   - Move logging setup into `core/logging.py` with a `configure_logging(level: str)` helper invoked by `main.py`.

3. **Google Cloud DNS client**
   - Wrap service-account loading and `build('dns', 'v1')` creation inside `services/dns_client.py`.
   - Provide `get_dns_service(settings: Settings)` that caches the instantiated client per process.

4. **Domain services**
   - `dns_manager.py` handles `create_txt_record` / `delete_txt_record`, `parse_fqdn`, and returns structured responses.
   - `auth.py` provides `validate_api_key` and raises FastAPI `HTTPException` for invalid keys.

5. **API layer**
   - Introduce Pydantic models: `DNSChangeRequest`, `DNSChangeResponse`.
   - Build routers in `routes/health.py` and `routes/dns.py` with dependency injection for services.
   - Map endpoints: `GET /v1/health`, `GET /v1/live`, `POST /v1/dns/add`, `POST /v1/dns/remove`.
   - Keep 207 Multi-Status responses by returning `JSONResponse(status_code=207, content=[...])`.

6. **Application factory**
   - In `main.py`, instantiate FastAPI, include routers (`/v1` prefix), and configure lifespan startup to load settings + DNS client.
   - Export `app` for Gunicorn (`gunicorn -k uvicorn.workers.UvicornWorker app.main:app`).

7. **Testing**
   - Add unit tests for `parse_fqdn`, auth, and error handling using pytest and FastAPI’s TestClient.
   - Provide integration test harness in `docs/container_testing.md` referencing new FastAPI app paths.

8. **Dependencies & tooling**
   - Update `requirements.txt` with `fastapi`, `uvicorn[standard]`, `gunicorn`.
   - Consider `pre-commit` or `ruff` for linting to enforce modern style.

9. **Dockerfile refresh**
   - Rebase onto an image that already ships the Google Cloud SDK (e.g., `google/cloud-sdk:slim`) or add a dedicated SDK layer in a multi-stage build so Python dependencies install on a more full-featured Debian/Ubuntu base.
   - Convert the Dockerfile to a multi-stage build: one stage for installing system deps + Python packages, and a final runtime stage with only the application, SDK, and gunicorn entrypoint.
   - Run the container as a non-root user, expose only port 8080, and keep the entrypoint `["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8080", "app.main:app"]`. Mount config and service-account paths read-only so compromised processes cannot modify credentials.

10. **CI / quality gates**
    - Add a CI workflow (GitHub Actions, GitLab CI, etc.) running `ruff` or `flake8`, `black`, and `pytest`, plus FastAPI TestClient integration tests.
    - Optionally publish coverage reports and enforce minimum thresholds.

11. **Documentation updates**
   - Refresh README sections describing the FastAPI app, automatic OpenAPI docs at `/docs`, and new project layout.
   - Extend `docs/gprox.py.md` to reflect module-level changes or replace it with more granular docs per package.

12. **Observability**
    - Structured logging: emit JSON logs (e.g., via `structlog` or `python-json-logger`) with fields like `endpoint`, `fqdn`, `managed_zone`, and `request_id`, and forward them to Cloud Logging or your aggregator.
    - Metrics: instrument FastAPI with Prometheus (`prometheus-client` or `prometheus-fastapi-instrumentator`). Expose `/metrics` and add counters/histograms for DNS operations. If running multiple Gunicorn workers, configure Prometheus multiprocess mode or a proxy to aggregate metrics across workers.
    - Distributed tracing (optional): leverage OpenTelemetry instrumentation for FastAPI and the Google API client to send traces to Cloud Trace or another backend so DNS changes can be correlated end-to-end.

---

## Deployment Notes
- Docker entrypoint should switch to `["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8080", "app.main:app"]`.
- Ensure service account JSON and config file paths remain mountable exactly as before; FastAPI should pull the same settings.
- Monitor startup logs to confirm FastAPI lifespan events load configuration and Google credentials successfully.

Following this plan keeps functionality intact while yielding a modular, testable, and modern FastAPI-based service that is easier to maintain long-term.
