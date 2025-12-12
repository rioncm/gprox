### **FastAPI Application Overview**

The original monolithic `gprox.py` script has been replaced with a modular FastAPI project. This document summarizes the major modules, how they interact, and where core functionality lives.

- **Observability (`app/observability/metrics.py`)**
  - Defines Prometheus counters (e.g., `gprox_dns_requests_total`) referenced by services and exposed through the FastAPI instrumentation.

---

## **Core Modules (`app/core`)**

- **`config.py`**
  - Loads YAML configuration from `GPROX_CONFIG_PATH` (defaults to `/etc/gprox/config.yaml`) using Pydantic for validation.
  - Exposes `Settings` (log level, Google Cloud information, managed zones, API keys, TTL) and a cached `get_settings()` helper for dependency injection.

- **`logging.py`**
  - Provides `configure_logging(level)` which normalizes the desired log level and applies a consistent log format for the entire service.

---

## **Service Layer (`app/services`)**

- **`dns_client.py`**
  - Wraps Google service-account initialization and `googleapiclient.discovery.build('dns', 'v1')`.
  - Caches the DNS client per service-account path, minimizing repeated auth initialization.

- **`dns_manager.py`**
  - Contains the domain logic for parsing `_acme-challenge.` FQDNs, resolving managed zones, and orchestrating TXT record creation/deletion.
  - Methods:
    - `add_txt_record(fqdn, value)` and `remove_txt_record(fqdn, value)` return the list of response objects used by the API.
    - Internal helpers `_create_txt_record` and `_delete_txt_record` call Google Cloud DNS APIs, mirroring the behavior from the legacy script.
  - Emits Prometheus counters through `app.observability.metrics.dns_requests_total` to track operation successes/failures.

- **`auth.py`**
  - Provides `require_api_key(api_key, settings)` which raises a FastAPI `HTTPException` if the supplied key is missing from the configured list.

---

## **API Layer (`app/api`)**

- **`models.py`**
  - Defines the Pydantic schemas `DNSChangeRequest` and `DNSChangeResponse` used by the `/v1/dns/*` endpoints.

- **`deps.py`**
  - FastAPI dependency providers that inject `Settings` and `DNSManager` instances into route handlers.

- **Routes**
  - `routes/health.py`: Implements `GET /v1/health` and `GET /v1/live` for liveness/readiness checks.
  - `routes/dns.py`: Implements `POST /v1/dns/add` and `POST /v1/dns/remove`. Each endpoint enforces API-key validation and delegates to `DNSManager`, returning `207 Multi-Status` responses to remain backward compatible.

---

## **Application Entrypoint (`app/main.py`)**

- Houses the FastAPI factory and an async `lifespan` context manager that:
  - Loads configuration,
  - Configures logging,
  - Primes the Google Cloud DNS client.
- Registers routers, exposes OpenAPI docs at `/docs`, and exports `app` for Gunicorn/Uvicorn workers.
- Integrates `prometheus-fastapi-instrumentator` to expose HTTP metrics at `/metrics`.

---

## **Key Behaviors Preserved**

- Endpoint surface (`/v1/health`, `/v1/live`, `/v1/dns/add`, `/v1/dns/remove`).
- Use of API keys for authentication.
- Managed-zone parsing logic to safeguard allowed DNS zones.
- Multi-status responses with detailed per-request information.

With this structure, each layer (config, services, API) can be unit-tested independently, FastAPI can auto-generate documentation, and the application is ready for modern deployment patterns (Gunicorn workers, Prometheus/OTel instrumentation, etc.).
