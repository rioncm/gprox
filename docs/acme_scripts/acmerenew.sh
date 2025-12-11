#!/bin/bash

# This script renews and deploys the certificate for HOST.example.com using acme.sh on Synology DSM. Tested on DSM 7.0.1-42218 Update 4.
# It includes debug logging for troubleshooting.

# the original creation usde the acme directory in /usr/local/share/acme.sh for certificate storage with the --home $PWD option

# This script should be installed in the Synology DSM in directory suitable for running scripts and made executable.

# This script renews and deploys the certificate for HOST.example.com using acme.sh
# It includes debug logging for troubleshooting

# Exit on error
set -e

# Configuration
ACME_HOME="/usr/local/share/acme.sh"
DOMAIN="HOST.example.com" # Change this to your host/domain
ACME_COMMAND="$ACME_HOME/acme.sh"
DEPLOY_HOOK="synology_dsm"
LOG_FILE="/var/log/acme_renew_debug.log"

# Logging function
log() {
  echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Check if acme.sh exists
if [ ! -x "$ACME_COMMAND" ]; then
  log "ERROR: acme.sh command not found at $ACME_COMMAND"
  exit 1
fi

# Renew the certificate with debug logging
log "Starting certificate renewal for $DOMAIN with debug..."
if $ACME_COMMAND --renew -d "$DOMAIN" --home "$ACME_HOME" --dns dns_gprox --server letsencrypt --debug 2>&1 | tee -a "$LOG_FILE"; then
  log "Certificate renewal succeeded for $DOMAIN."
else
  log "ERROR: Certificate renewal failed for $DOMAIN."
  exit 1
fi

# Deploy the certificate with debug logging
log "Starting certificate deployment for $DOMAIN using deploy hook $DEPLOY_HOOK with debug..."
if $ACME_COMMAND --deploy -d "$DOMAIN" --deploy-hook "$DEPLOY_HOOK" --home "$ACME_HOME" --debug 2>&1 | tee -a "$LOG_FILE"; then
  log "Certificate deployment succeeded for $DOMAIN."
else
  log "ERROR: Certificate deployment failed for $DOMAIN."
  exit 1
fi

log "Certificate renewal and deployment completed successfully for $DOMAIN."