### **Code Documentation for `gprox.py`**

Below is a detailed explanation and documentation of the `gprox.py` script. The script provides a RESTful API to add and remove TXT records for DNS challenges in Google Cloud DNS.

---

### **Modules Used**
- **`flask`**: Provides the web server and routing functionality for the API.
- **`logging`**: Handles logging for debugging and error tracking.
- **`yaml`**: Parses the configuration file.
- **`os`**: Accesses environment variables.
- **`googleapiclient.discovery`**: Interacts with Google Cloud DNS APIs.
- **`google.oauth2.service_account`**: Authenticates using Google Cloud service account credentials.
- **`ipaddress`**: (Currently unused but included) Handles IP validation for possible future network security checks.

---

### **Core Components**

#### 1. **Configuration Loading (`load_config`)**
- **Purpose**: Loads the configuration file (`config.yaml`) from the path specified in the `GPROX_CONFIG_PATH` environment variable.
- **Error Handling**:
  - Raises an exception if the file is missing or incorrectly formatted.
- **Configuration Keys**:
  - `log_level`: Logging level (e.g., DEBUG, INFO).
  - `gcloud_service_account`: Path to the Google Cloud service account JSON file.
  - `gcloud_project`: Google Cloud project ID.
  - `managed_zones`: Dictionary mapping zone names to domain names.
  - `api_keys`: List of valid API keys.
  - `ttl`: Default TTL for DNS records.

#### 2. **Logging Setup**
- **Purpose**: Configures logging based on the `log_level` from the configuration.
- **Logging Levels**:
  - `DEBUG`: Detailed logs for debugging.
  - `INFO`: General information.
  - `WARNING`: Non-critical issues.
  - `ERROR`: Critical errors.

#### 3. **Google Cloud DNS Service Initialization (`get_dns_service`)**
- **Purpose**: Authenticates with Google Cloud using the service account file and initializes the Google Cloud DNS API client.
- **Error Handling**:
  - Logs and raises errors if the service account file is missing or invalid.

#### 4. **Health Check (`/v1/health`)**
- **Endpoint**: `GET /v1/health`
- **Purpose**: Returns a simple status response (`{"status": "ok"}`) to confirm the API is running.

---

### **Core Endpoints**

#### **1. Add TXT Record (`/v1/dns/add`)**
- **Endpoint**: `POST /v1/dns/add`
- **Input**:
  - `api_key` (string): API key for authentication.
  - `fqdn` (string): Fully qualified domain name (e.g., `_acme-challenge.domain.com`).
  - `value` (string): Value of the TXT record.
- **Response**:
  - `207 Multi-Status`: Provides a per-FQDN status for the request.
- **Logic**:
  1. Validates the `api_key`.
  2. Parses the `fqdn` to determine the matching managed zone.
  3. Sends the request to Google Cloud DNS to create the TXT record.
- **Error Handling**:
  - Invalid API keys or FQDNs result in specific error messages.

#### **2. Remove TXT Record (`/v1/dns/remove`)**
- **Endpoint**: `POST /v1/dns/remove`
- **Input**:
  - `api_key` (string): API key for authentication.
  - `fqdn` (string): Fully qualified domain name.
  - `value` (string): Value of the TXT record to remove.
- **Response**:
  - `207 Multi-Status`: Provides a per-FQDN status for the request.
- **Logic**:
  1. Validates the `api_key`.
  2. Parses the `fqdn` to determine the matching managed zone.
  3. Sends the request to Google Cloud DNS to delete the TXT record.
- **Error Handling**:
  - Similar to the add endpoint, with specific messages for invalid API keys or unmatched FQDNs.

---

### **Helper Functions**

#### **`validate_fqdn(fqdn)`**
- **Purpose**: Validates that an FQDN belongs to a managed zone defined in the configuration.
- **Logic**:
  - Checks if the FQDN ends with a known domain from `managed_zones`.
- **Returns**: `True` if valid, `False` otherwise.

#### **`create_txt_record(project_id, managed_zone, record_name, txt_value)`**
- **Purpose**: Sends a request to Google Cloud DNS to create a TXT record.
- **Input**:
  - `project_id`: Google Cloud project ID.
  - `managed_zone`: Name of the managed zone.
  - `record_name`: Full FQDN for the record.
  - `txt_value`: Value of the TXT record.
- **Returns**: API response on success.
- **Error Handling**:
  - Logs and raises exceptions for API or internal errors.

#### **`delete_txt_record(project_id, managed_zone, record_name, txt_value)`**
- **Purpose**: Sends a request to Google Cloud DNS to delete a TXT record.
- **Input**:
  - Same as `create_txt_record`.
- **Returns**: API response on success.
- **Error Handling**:
  - Similar to `create_txt_record`.

#### **`parse_fqdn(fqdn)`**
- **Purpose**: Determines the managed zone for a given FQDN.
- **Logic**:
  1. Ensures the FQDN starts with `_acme-challenge.`.
  2. Strips the prefix and trailing dot.
  3. Iterates through possible domain matches in `managed_zones`.
- **Returns**: The name of the matching managed zone.
- **Raises**: `ValueError` if no match is found.

#### **`is_api_key_valid(api_key)`**
- **Purpose**: Checks if an API key is valid.
- **Input**: `api_key` from the request.
- **Logic**:
  - Compares the key against the `api_keys` list in the configuration.
- **Returns**: `True` if valid, `False` otherwise.

---

### **Key Features**

- **API Security**:
  - Uses API keys to restrict access. Keys are validated against a list in `config.yaml`.
- **Multi-FQDN Support**:
  - The `add` and `remove` endpoints handle multiple FQDNs in a single request.
- **Logging**:
  - Detailed logs for debugging and tracking API usage.
- **Google Cloud Integration**:
  - Fully integrates with Google Cloud DNS using service account credentials.
- **Configuration-Driven**:
  - Highly customizable via `config.yaml`.

---

### **Potential Enhancements for the future**
1. **Rate Limiting**:
   - Prevent abuse by adding rate limits per API key.
2. **IP Whitelisting**:
   - Restrict requests to specific IP ranges for additional security.
3. **Health Metrics**:
   - Add detailed metrics for monitoring (e.g., request counts, success rates).
4. **Improved Validation**:
   - Enhance validation for `fqdn` and `value` inputs.

This documentation provides a comprehensive overview of the `gprox.py` script. Let me know if further details are required!