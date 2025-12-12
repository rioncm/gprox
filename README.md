

# **GPROX: An ACME DNS Proxy for Google Cloud DNS**

GPROX is a lightweight ACME DNS proxy specifically designed to work seamlessly with [Google Cloud DNS](https://cloud.google.com/dns) and [acme.sh](https://github.com/acmesh-official/acme.sh). The primary goal is to enable DNS challenges for generating universally recognized SSL certificates, especially for systems like Synology NAS, where the built-in Let’s Encrypt method does not support DNS challenges.

---

## **Purpose**

This project was created to overcome the limitations of Synology’s built-in SSL certificate provisioning system. While tools like `dns_acmeproxy.sh` exist, configuration challenges and compatibility issues led to the creation of GPROX, a tailored solution for working with Google Cloud DNS and supporting Synology DSM.

GPROX acts as a secure intermediary between `acme.sh` and Google Cloud DNS, facilitating DNS-based validation for SSL certificates in an efficient, reliable, and customizable manner.

---

## **Key Features**

- **ACME DNS Challenge Proxy**:
  - Handles DNS challenges required by Let’s Encrypt for SSL certificate issuance.
  - Compatible with `acme.sh`'s DNS API.

- **Google Cloud DNS Integration**:
  - Directly interacts with Google Cloud DNS using service account credentials.
  - Automates TXT record creation and deletion.

- **API Security**:
  - API key authentication ensures secure access.
  - Designed to run behind reverse proxies like Traefik.

- **Lightweight and Flexible**:
  - Implemented with FastAPI behind Gunicorn/Uvicorn workers for production readiness.
  - Configurable via YAML for custom domains, TTL, and API key management.

- **Built-in Metrics**:
  - Exposes Prometheus-compatible metrics at `/metrics`, including per-operation counters for TXT record changes.

- **Extensible**:
  - Built with simplicity in mind, allowing contributors to add features like rate limiting, IP whitelisting, and more.

---

## **Project Components**

### **1. FastAPI Application (`app/`)**
The API is implemented as a modular FastAPI project. Key modules include:

- `app/main.py`: Application factory, router registration, and lifespan hooks that initialize configuration and the Google Cloud DNS client.
- `app/api/routes/*`: Route modules for health checks and DNS operations built with FastAPI routers.
- `app/services/*`: Domain services for authentication, DNS parsing, and Google Cloud interactions.
- `app/core/*`: Configuration loading (YAML + Pydantic) and logging helpers.

- **Key Endpoints**:
  - `POST /v1/dns/add`: Add a TXT record.
  - `POST /v1/dns/remove`: Remove a TXT record.
  - `GET /v1/health`: Check API health.

### Service Account Key (`gcloud.json`)
The `gcloud.json` file contains the credentials for a Google Cloud service account with permissions to manage Cloud DNS. Ensure the service account has the `roles/dns.admin` role and securely store the JSON file. For detailed instructions on creating this file, see the [gcloud.json.md](gcloud.json.md) guide.

 
- **Highlights**:
  - Validates API keys before processing requests.
  - Parses Fully Qualified Domain Names (FQDNs) to determine the correct Google Cloud DNS managed zone.
  - Uses Google Cloud DNS APIs to handle DNS record operations.

### **2. `dns_gprox.sh`**
A custom DNS API script for `acme.sh` to interact with GPROX.

- **Usage**:
  - Add a TXT record: `dns_gprox_add`.
  - Remove a TXT record: `dns_gprox_rm`.
  
- **Configuration**:
  - Requires `GPROX_ENDPOINT` and `GPROX_API_KEY` as environment variables.

### **3. `acmerenew.sh`**
A helper script for automating SSL certificate renewal and deployment.

- **Features**:
  - Leverages `acme.sh` for certificate renewal.
  - Deploys renewed certificates to Synology DSM via the `synology_dsm` deploy hook.
  
---

## **Getting Started**
### Getting Started



### **1. Prerequisites**
- A Google Cloud project with DNS API enabled.
- A service account with `roles/dns.admin` permissions.
- Synology DSM with SSH enabled (optional, for initial setup).
- Docker installed for running GPROX.

### **2. Installation**

#### **Deploy GPROX**
1. Clone this repository and navigate to the project directory.
2. Build the Docker image:
   ```bash
   docker build -t gprox .
   ```
3. Configure the `config.yaml` file with your managed zones, API keys, and other settings. See the example file included in this repository for details.
4. Create a service account and download the corresponding `gcloud.json` file. Refer to the [gcloud.json.md](gcloud.json.md) guide for instructions.

5. Run the container:
   ```bash
   docker run -d --name gprox -p 8080:8080 \
     -v /path/to/config.yaml:/etc/gprox/config.yaml:ro \
     -v /path/to/google.json:/etc/gprox/google.json:ro \
     gprox
   ```

#### **Install `acme.sh`**
1. Install `acme.sh`:
   ```bash
   curl https://get.acme.sh | sh
   ```
2. Copy `dns_gprox.sh` to the `dnsapi` directory of `acme.sh`:
   ```bash
   cp /path/to/dns_gprox.sh ~/.acme.sh/dnsapi/
   ```

#### **Configure Synology DSM** *(Optional)*
1. Follow the instructions in `acmerenew.sh` to add your domain.
2. Schedule a task to renew and deploy certificates.

---

## **Configuration**

The `config.yaml` file is the heart of GPROX. Below is an example:

### Managed Zones
The `managed_zones` in `config.yaml` define the DNS zones that the proxy is allowed to modify. This acts as an additional security layer to ensure no unauthorized DNS zones are accessed. For example:
```yaml
managed_zones:
  example-com: example.com
  anotherexample-example-com: anotherexample.example.com


```yaml
log_level: "INFO"
gcloud_service_account: "/path/to/service_account.json"
gcloud_project: "your-google-cloud-project-id"
managed_zones:
  example-zone: "example.com."
  another-zone: "another.com."
api_keys:
  - "your-api-key"
ttl: 300
```

- **`log_level`**: Adjust logging verbosity (`DEBUG`, `INFO`, `ERROR`).
- **`gcloud_service_account`**: Path to your Google Cloud service account JSON file.
- **`gcloud_project`**: Google Cloud project ID.
- **`managed_zones`**: Define your DNS managed zones.
- **`api_keys`**: List of valid API keys for authenticating requests.

---

## **Usage**

### **1. Issue a Certificate**
Run `acme.sh` with the `dns_gprox` DNS API:
```bash
acme.sh --server letsencrypt --issue -d "example.com" --dns dns_gprox
```

### **2. Deploy to Synology DSM**
Deploy the certificate using the `synology_dsm` deploy hook:
```bash
acme.sh --deploy -d "example.com" --deploy-hook synology_dsm
```

### **3. Renew Certificates**
Automate renewal and deployment using `acmerenew.sh` in a scheduled task.

---

## **Observability & Metrics**

- **Prometheus endpoint**: FastAPI instrumentation exposes metrics at `GET /metrics`. Default counters include HTTP request stats plus `gprox_dns_requests_total{operation,result=...}` recording TXT add/remove successes and failures.
- **Scraping in Kubernetes/Docker**: Ensure the `/metrics` path is reachable by your Prometheus scrape jobs. When running Gunicorn with multiple workers or replicas, deploy Prometheus in multiprocess mode (set `PROMETHEUS_MULTIPROC_DIR` and mount a writable tmpfs) so metrics from each worker are aggregated correctly.
- **Logging**: Standardized structured logging can be forwarded to Google Cloud Logging or another aggregator. Configure log levels through `config.yaml`.

---

## **Releases & Container Publishing**

Publishing a GitHub release automatically builds and pushes an image to the `blue-platypus` organization on the GitHub Container Registry (GHCR). The workflow defined in `.github/workflows/release.yml` performs the following whenever a release is published:

- Uses the repository Dockerfile to build an image.
- Tags the image with the release tag (e.g., `v1.2.3`), semantic variants (`1.2`, `1`), `latest`, and the commit SHA.
- Pushes the image to `ghcr.io/blue-platypus/gprox`.

### **Prerequisites**
- Push this repository to the `blue-platypus` GitHub organization.
- In the repository settings, ensure the default `GITHUB_TOKEN` has permission to write packages (Settings ➜ Actions ➜ General ➜ Workflow permissions).
- After the first push, mark the `ghcr.io/blue-platypus/gprox` package as public in the GitHub UI so others can pull it.

### **Release Flow**
1. Tag the commit you want to release, e.g., `git tag v1.2.3 && git push origin v1.2.3`.
2. Draft and publish a GitHub Release that uses that tag. Once the release status is “published,” the workflow runs automatically.
3. Monitor the workflow run in the “Actions” tab to confirm the build and push succeeded.
4. Pull the public image with `docker pull ghcr.io/blue-platypus/gprox:latest` or the exact release tag.

You can also run the workflow manually from the “Actions” tab via **Run workflow** to produce ad-hoc builds (they are tagged with the commit SHA and `latest`).

---

## **Security Considerations**

- **API Key Management**:
  - Rotate API keys regularly.
  - Use unique keys for each user.

### API Keys
- **Management**: API keys are defined in `config.yaml`. Use a consistent format for keys that includes the purpose or user (e.g., `<key>_<user>`).
- **Logging Behavior**: API keys are logged when used, allowing traceability. Avoid using sensitive identifiers in key names.

  
- **Service Account Security**:
  - Limit permissions to only DNS operations (`roles/dns.admin`).
  - Restrict access to the service account file.

- **Rate Limiting and IP Restrictions**:
  - Consider implementing rate limiting or IP whitelisting for additional security.

- **HTTPS**:
  - Run GPROX behind a reverse proxy like Traefik for SSL termination.

---

## **References and Inspiration**

- [Synology DSM 7 with Let’s Encrypt and DNS Challenge](https://dr-b.io/post/Synology-DSM-7-with-Lets-Encrypt-and-DNS-Challenge)
- [acme.sh Documentation](https://github.com/acmesh-official/acme.sh)
- `dns_myapi.sh` example from [acme.sh](https://github.com/acmesh-official/acme.sh/blob/master/dnsapi/dns_myapi.sh)
- Extensive support from ChatGPT during development.

---

### Debugging
If issues arise during certificate issuance or deployment, use the `--debug` flag with `acme.sh` for verbose logging:
```bash
./acme.sh --issue -d example.com --dns dns_gprox --debug
```

## **Contributing**

Contributions are welcome! If you have ideas for features like rate limiting or IP whitelisting, please open an issue or submit a pull request. For major changes, reach out to discuss the design.

### Security Considerations
- **API Key Management**:
  - Rotate API keys periodically to minimize security risks.
- **Service Account Security**:
  - Regularly review and rotate service account credentials.
  - Limit the service account’s permissions to only what is necessary (e.g., `roles/dns.admin`).


---

## **License**

This project is licensed under the [MIT License](LICENSE).

---

Let me know if you’d like any adjustments or additional details!
