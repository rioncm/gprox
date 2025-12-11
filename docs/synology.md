Here’s the revised and detailed documentation, formatted in **Markdown** for better readability, with grammar corrections, expanded details, and additional explanations.

---

# Using `dns_gprox.sh` and `acmerenew.sh` on a Synology System

This guide explains how to configure and use the `dns_gprox.sh` and `acmerenew.sh` scripts on a Synology NAS to manage SSL certificates with ACME and deploy them for Synology services.

---

## **Prerequisites**

1. **Install and Configure GPROX**:
   Ensure the GPROX API is set up and operational. The `dns_gprox.sh` script communicates with GPROX to manage DNS challenges.

2. **Enable SSH on Synology**:
   SSH access is required for configuration. Once set up, you can disable SSH if preferred.

3. **Download and Prepare Scripts**:
   Upload the `dns_gprox.sh` and `acmerenew.sh` scripts to your Synology NAS. For example:
   - Create a shared folder called `scripts` using the Synology UI.
   - Place the scripts in `/volume1/scripts` (or another path of your choice).

---

## **Steps**

### **1. Create a User for Automation (Optional)**

For security and better management, create a dedicated user (e.g., `acmessl`) to execute the scripts.

- Log in to the Synology DSM web interface.
- Go to **Control Panel > User > Create**:
  1. Assign a username (e.g., `acmessl`).
  2. Add the user to the `administrators` and `http` groups.
  3. Disable 2FA for this user to avoid automation issues.
  4. Leave other settings at their defaults.

### **2. Install `acme.sh`**

Log in to the Synology system via SSH as the user created above (or an administrator account). Run the following commands to install `acme.sh`:

```bash
wget -O /tmp/acme.sh.zip https://github.com/acmesh-official/acme.sh/archive/master.zip &&
sudo 7z x -o/usr/local/share /tmp/acme.sh.zip &&
sudo mv /usr/local/share/acme.sh-master/ /usr/local/share/acme.sh &&
sudo chown -R YOURUSER /usr/local/share/acme.sh/ &&
cd /usr/local/share/acme.sh
```

### **3. Copy `dns_gprox.sh` to the DNSAPI Directory**

Copy the `dns_gprox.sh` script to the appropriate directory in `acme.sh`:

```bash
cp /volume1/scripts/dns_gprox.sh ./dnsapi/dns_gprox.sh
```

Make the script executable:

```bash
chmod +x ./dnsapi/dns_gprox.sh
```

### **4. Set Environment Variables**

Set the required environment variables for both the GPROX API and Synology DSM deployment. Add these variables to the user's `.bashrc` or `.profile` file for persistence.

```bash
# Required for GPROX
export GPROX_ENDPOINT="http(s)://your-gprox-continer.example.com"
export GPROX_API_KEY="gprox_user_defind_api_key"

# Required for Synology Deploy Hook
export SYNO_USERNAME="acmessl"                # The Synology user created earlier
export SYNO_PASSWORD="REALLySeCUrEP@ssWorD"  # The user's password
export SYNO_CERTIFICATE="default"            # The certificate name in Synology DSM
export SYNO_CREATE=0                         # Create a new certificate (0 = No, 1 = Yes)
export SYNO_SCHEME="http"                    # HTTP or HTTPS
export SYNO_HOSTNAME="localhost"             # Synology hostname
export SYNO_PORT="5000"                      # DSM port (5000 for HTTP, 5001 for HTTPS)
```

#### **Explanation of Variables**:
- **`GPROX_ENDPOINT`**: URL of the GPROX API.
- **`GPROX_API_KEY`**: API key for authenticating with GPROX.
- **Synology-Specific Variables**:
  - `SYNO_CERTIFICATE`: Name of the certificate in Synology DSM (use "default" to replace the default certificate).
  - `SYNO_CREATE`: If `1`, creates a new certificate in the process; if `0`, use the existing one you just created.
  - `SYNO_HOSTNAME`, `SYNO_PORT`: Used to connect to Synology DSM locally.

Reload the environment variables:
```bash
source ~/.bashrc
```

### **5. Issue the Certificate**

Run the following command to issue a certificate for your domain(s):

```bash
./acme.sh --server letsencrypt --issue -d "joshuatree.pminc.me" -d "jtree.pminc.me" --dns dns_gprox --home $PWD
```

#### **Command Flags**:
- `--server letsencrypt`: Use Let’s Encrypt as the ACME server. Other are available.
- `-d "domain"`: Specify the primary domain and additional SANs.
- `--dns dns_gprox`: Use the `dns_gprox.sh` script for DNS validation.
- `--home $PWD`: Specify the home directory for `acme.sh` setting and files. 

### **6. Deploy the Certificate**

Deploy the issued certificate to Synology DSM using the deploy hook:

```bash
./acme.sh --deploy -d "joshuatree.pminc.me" --deploy-hook synology_dsm --home $PWD --debug
```

#### **Command Flags**:
- `--deploy`: Deploy the certificate.
- `--deploy-hook synology_dsm`: Use the Synology DSM deployment hook.
- `--debug`: Log additional details for debugging.

### **7. Verify and Apply the Certificate**

- Log in to the Synology DSM interface.
- Navigate to **Control Panel > Security > Certificates**.
- Verify the newly deployed certificate is listed.
- Apply the certificate to the desired services by clicking **Settings**. This will restart the associated services automatically.

### **8. Edit and Configure `acmerenew.sh`**

- Edit the configuration section of `acmerenew.sh` script to include your domain and settings. Generally yhe domain is the only section that needs to be edited. 
- Example `acmerenew.sh` command for renewal:
  
  ```bash
 # Configuration
ACME_HOME="/usr/local/share/acme.sh"
DOMAIN="YOUR_HOST.DOMAIN.TLD"
ACME_COMMAND="$ACME_HOME/acme.sh"
DEPLOY_HOOK="synology_dsm"
LOG_FILE="/var/log/acme_renew_debug.log"
  ```
- Make the script executable  
```bash
chmod +x /volume1/scripts/acmerenew.sh
```

### **9. Schedule Automatic Renewal**

- Go to **Control Panel > Task Scheduler**.
- Create a task to run the `acmerenew.sh` script:
  - **Task Type**: Scheduled Task > User-defined Script
  - **Run Command**:
    ```bash
    /volume1/scripts/acmerenew.sh
    ```
  - **Schedule**: Run every 85 days and repeat every 3 months.

---

## **Additional Notes**

- **Log Files**:
  - Add logging to your `acmerenew.sh` script to capture renewal details.
  - Example:
    ```bash
    ./acme.sh --renew -d "joshuatree.pminc.me" --home /usr/local/share/acme.sh --dns dns_gprox --server letsencrypt >> /var/log/acme_renew.log 2>&1
    ```

- **Service Restarts**:
  - Ensure the services using the certificate are restarted after deployment.

