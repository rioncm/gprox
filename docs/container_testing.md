Here’s a concise guide for using `curl` to interact with the GPROX container. It includes examples for both HTTP and HTTPS requests.

---

# **Using `curl` with GPROX**

This guide demonstrates how to use `curl` to send requests to the GPROX container for managing DNS TXT records.

---

## **Prerequisites**
1. **API Endpoint**: Ensure the GPROX container is running and accessible.
   - Example endpoints:
     - HTTP: `http://gprox.example.com`
     - HTTPS: `https://gprox.example.com`
2. **API Key**: Obtain a valid API key from the `config.yaml`.

---

## **Endpoints Overview**

- **Health Check**: `GET /v1/health`
- **Health Check**: `GET /v1/live`
- **Add TXT Record**: `POST /v1/dns/add`
- **Remove TXT Record**: `POST /v1/dns/remove`

---

## **Examples**

### **1. Health Check**
#### HTTP:
```bash
curl -X GET http://gprox.example.com/v1/health
```

#### HTTPS:
```bash
curl -X GET https://gprox.example.com/v1/health
```

---

### **2. Add a TXT Record**
#### Payload Example:
```json
{
  "fqdn": "_acme-challenge.example.com",
  "value": "sample-token",
  "api_key": "your-api-key"
}
```

#### HTTP:
```bash
curl -X POST http://gprox.example.com/v1/dns/add \
-H "Content-Type: application/json" \
-d '{
  "fqdn": "_acme-challenge.example.com",
  "value": "sample-token",
  "api_key": "your-api-key"
}'
```

#### HTTPS:
```bash
curl -X POST https://gprox.example.com/v1/dns/add \
-H "Content-Type: application/json" \
-d '{
  "fqdn": "_acme-challenge.example.com",
  "value": "sample-token",
  "api_key": "your-api-key"
}'
```

---

### **3. Remove a TXT Record**
#### Payload Example:
```json
{
  "fqdn": "_acme-challenge.example.com",
  "value": "sample-token",
  "api_key": "your-api-key"
}
```

#### HTTP:
```bash
curl -X POST http://gprox.example.com/v1/dns/remove \
-H "Content-Type: application/json" \
-d '{
  "fqdn": "_acme-challenge.example.com",
  "value": "sample-token",
  "api_key": "your-api-key"
}'
```

#### HTTPS:
```bash
curl -X POST https://gprox.example.com/v1/dns/remove \
-H "Content-Type: application/json" \
-d '{
  "fqdn": "_acme-challenge.example.com",
  "value": "sample-token",
  "api_key": "your-api-key"
}'
```

---

## **Notes**

1. **Replace Placeholders**:
   - Replace `gprox.example.com` with your actual endpoint.
   - Replace `your-api-key` with a valid API key.

2. **HTTPS**:
   - Ensure your reverse proxy (e.g., Traefik) or GPROX container is configured for SSL termination.

3. **Debugging**:
   - Use the `-v` flag for verbose output:
     ```bash
     curl -v -X GET https://gprox.example.com/v1/health
     ```

---

This concise guide should help you quickly interact with the GPROX container using `curl`. Let me know if further details are needed!