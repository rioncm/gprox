from flask import Flask, request, jsonify
import logging
import yaml
import os
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2 import service_account
import ipaddress

app = Flask(__name__)

# Load configuration
def load_config():
    config_path = os.environ.get('GPROX_CONFIG_PATH', '/etc/gprox/config.yaml')
    logger.debug(f"Loading configuration from {config_path}")
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {config_path}")
        raise
    except yaml.YAMLError as e:
        logger.error(f"Error parsing configuration file: {e}")
        raise

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

try:
    config = load_config()
except Exception as e:
    logger.error(f"Failed to load configuration: {e}")
    raise

log_level = config.get('log_level', 'INFO').upper()
logger.setLevel(log_level)

# Initialize Google Cloud DNS service
def get_dns_service():
    try:
        credentials_path = config.get('gcloud_service_account')
        if not credentials_path or not os.path.isfile(credentials_path):
            logger.error(f"Google service account file is missing: {credentials_path}")
            raise ValueError("Service account file is not configured or does not exist")

        logger.debug(f"Using service account file: {credentials_path}")
        credentials = service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=['https://www.googleapis.com/auth/ndev.clouddns.readwrite']
        )
        return build('dns', 'v1', credentials=credentials)
    except Exception as e:
        logger.error(f"Failed to initialize Google Cloud DNS service: {e}")
        raise

dns_service = get_dns_service()

# Validate the domain in the FQDN
def validate_fqdn(fqdn):
    for _, domain in config.get('managed_zones', {}).items():
        if fqdn.endswith(domain + '.'):
            return True
    logger.warning(f"FQDN {fqdn} is not in the list of valid domains.")
    return False

# Health check
@app.route('/v1/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"})

#Live Check
@app.route('/v1/live', methods=['GET'])
def live():
    return jsonify({"status": "alive"})

# Add TXT Record
@app.route('/v1/dns/add', methods=['POST'])
def add_txt_record():
    
   
    data = request.get_json()
    logger.debug(f"Received add request: {data}")
    
    #validate api key for security
    api_key = data.get("api_key")
    if is_api_key_valid(api_key):
        logger.info(f"valid API key used {api_key} ")
    else:
        logger.debug(f"API key sent is {api_key}")
        return jsonify({"status": "error", "message": "Invalid API key"}), 403

    responses = []
    fqdn = data.get("fqdn") 
    value = data.get("value")

    if not fqdn or not value:
        logger.warning("Missing required fields 'fqdn' or 'value'")
        responses.append({"fqdn": fqdn, "status": "error", "message": "Missing required fields 'fqdn' or 'value'"})

    else:
        
        try:
            
            managed_zone = parse_fqdn(fqdn)
            record_name = fqdn  + "." #add a dot at the end of the record name for formatting
            txt_value = value
            project_id = config.get("gcloud_project")
            if not project_id:
                raise ValueError("gcloud_project is not configured")

            response = create_txt_record(project_id, managed_zone, record_name, txt_value)
            responses.append({"fqdn": fqdn, "status": "success", "message": "TXT record added successfully", "response": response})
        except ValueError as e:
            logger.warning(str(e))
            responses.append({"fqdn": fqdn, "status": "error", "message": str(e)})
        except HttpError as e:
            logger.error(f"Failed to add TXT record for {fqdn}: {e}")
            responses.append({"fqdn": fqdn, "status": "error", "message": "Failed to add TXT record"})
        except Exception as e:
            logger.error(f"Unexpected error for {fqdn}: {e}")
            responses.append({"fqdn": fqdn, "status": "error", "message": "An unexpected error occurred"})

    return jsonify(responses), 207

# Remove TXT Record
@app.route('/v1/dns/remove', methods=['POST'])
def remove_txt_record():

    
    data = request.get_json()
    logger.debug(f"Received remove request: {data}")

    #validate api key for security
    api_key = data.get("api_key")
    if is_api_key_valid(api_key):
        logger.info(f"valid API key used {api_key} ")
    else:
        logger.debug(f"API key sent is {api_key}")
        return jsonify({"status": "error", "message": "Invalid API key"}), 403
        


    responses = []    
    fqdn = data.get("fqdn")
    value = data.get("value")
    if not fqdn or not value:
        logger.warning("Missing required fields 'fqdn' or 'value'")
        responses.append({"fqdn": fqdn, "status": "error", "message": "Missing required fields 'fqdn' or 'value'"})
        
    else:
        

        try:
            
            managed_zone = parse_fqdn(fqdn)
            record_name = fqdn + "." #add a dot at the end of the record name for formatting
            txt_value = value
            project_id = config.get("gcloud_project")
            if not project_id:
                raise ValueError("gcloud_project is not configured")

            response = delete_txt_record(project_id, managed_zone, record_name, txt_value)
            responses.append({"fqdn": fqdn, "status": "success", "message": "TXT record removed successfully", "response": response})
        except ValueError as e:
            logger.warning(str(e))
            responses.append({"fqdn": fqdn, "status": "error", "message": str(e)})
        except HttpError as e:
            logger.error(f"Failed to remove TXT record for {fqdn}: {e}")
            responses.append({"fqdn": fqdn, "status": "error", "message": "Failed to remove TXT record"})
        except Exception as e:
            logger.error(f"Unexpected error for {fqdn}: {e}")
            responses.append({"fqdn": fqdn, "status": "error", "message": "An unexpected error occurred"})

    return jsonify(responses), 207


# Google Cloud DNS TXT record creation
def create_txt_record(project_id, managed_zone, record_name, txt_value):
    body = {
        "kind": "dns#resourceRecordSet",
        "name": record_name,
        "type": "TXT",
        "ttl": config.get("ttl", 300),
        "rrdatas": [f"\"{txt_value}\""]
    }

    try:
        logger.debug(f"Attempting to add TXT record: {body}")
        request = dns_service.resourceRecordSets().create(
            project=project_id, managedZone=managed_zone, body=body
        )
        response = request.execute()
        logger.info(f"TXT record added: {record_name} with value {txt_value}")
        return response
    except Exception as e:
        logger.error(f"Failed to add TXT record: {e}")
        raise

# Google Cloud DNS TXT record deletion
def delete_txt_record(project_id, managed_zone, record_name, txt_value):
    body = {
        "kind": "dns#resourceRecordSet",
        "name": record_name,
        "type": "TXT",
        "ttl": config.get("ttl", 300),
        "rrdatas": [f"\"{txt_value}\""]
    }

    try:
        logger.debug(f"Attempting to delete TXT record: {body}")
        request = dns_service.changes().create(
            project=project_id,
            managedZone=managed_zone,
            body={
                "kind": "dns#change",
                "deletions": [body]
            }
        )
        response = request.execute()
        logger.info(f"TXT record removed: {record_name} with value {txt_value}")
        return response
    except Exception as e:
        logger.error(f"Failed to remove TXT record: {e}")
        raise


def parse_fqdn(fqdn):
    """
    Parses an FQDN and determines the associated managed zone from the configuration.

    Args:
        fqdn (str): Fully qualified domain name (e.g., _acme-challenge.host.subdomain.domain.tld).
        managed_zones (dict): Dictionary of managed zones from the configuration.

    Returns:
        tuple: (record_name, managed_zone) where:
            - record_name is the full FQDN for the TXT record.
            - managed_zone is the matching managed zone for the domain.

    Raises:
        ValueError: If the FQDN does not match any managed zone.
    """
    logger.debug(f"Parsing FQDN: {fqdn}")
    
    managed_zones = config.get('managed_zones', {})
    logger.debug(f"Managed zones: {managed_zones}")

    # Ensure the FQDN starts with "_acme-challenge."
    if not fqdn.startswith("_acme-challenge."):
        raise ValueError(f"Invalid FQDN format: {fqdn}")

    # Remove the "_acme-challenge." prefix
    stripped_fqdn = fqdn[len("_acme-challenge."):]
    logger.debug(f"Stripped FQDN: {stripped_fqdn}")

     # Check if the stripped FQDN matches a managed zone for wildcards
    for zone_name, zone_domain in managed_zones.items():
        if stripped_fqdn == zone_domain:
            return zone_name

      # Remove the trailing dot, if present
    if stripped_fqdn.endswith('.'):
        stripped_fqdn = stripped_fqdn[:-1]

    # Split the stripped FQDN into parts
    fqdn_parts = stripped_fqdn.split('.')
    logger.debug(f"FQDN parts: {fqdn_parts}")

    # Skip the host (first subdomain) and test remaining parts against managed zones
    for i in range(1, len(fqdn_parts)):
        possible_domain = '.'.join(fqdn_parts[i:])
        logger.debug(f"Testing possible domain: {possible_domain}")
        for zone_name, zone_domain in managed_zones.items():
            if possible_domain == zone_domain:
                logger.debug(f"Matched managed zone: {zone_name} for domain: {possible_domain}")
                return zone_name
            else: 
                logger.debug(f"No match for {possible_domain} against {zone_domain}")

    # No matching managed zone found
    logger.error(f"No managed zone found for FQDN: {fqdn}")
    raise ValueError(f"No managed zone found for FQDN: {fqdn}")


def is_api_key_valid(api_key):
    """
    Checks if the provided API key is valid.

    Args:
        api_key (str): The API key from the request header.

    Returns:
        bool: True if the API key is valid, False otherwise.
    """
    valid_keys = config.get("api_keys", [])
    if api_key in valid_keys:
        logger.debug(f"API key is valid: {api_key}")
        return True
    logger.warning(f"Invalid API key: {api_key}")
    return False


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)