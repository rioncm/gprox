"""
Domain logic for managing DNS TXT records.
"""

from __future__ import annotations

import logging
import ssl
from typing import Dict, List

from google.auth.exceptions import RefreshError, TransportError
from googleapiclient.errors import HttpError

from app.core.config import Settings
from app.observability.metrics import dns_requests_total

logger = logging.getLogger(__name__)


class DNSManager:
    def __init__(self, settings: Settings, dns_service):
        self.settings = settings
        self.dns_service = dns_service

    def add_txt_record(self, fqdn: str, value: str) -> List[Dict]:
        return self._handle_change("add", fqdn, value)

    def remove_txt_record(self, fqdn: str, value: str) -> List[Dict]:
        return self._handle_change("remove", fqdn, value)

    def _handle_change(self, operation: str, fqdn: str, value: str) -> List[Dict]:
        responses: List[Dict] = []

        if not fqdn or not value:
            logger.warning("Missing required fields 'fqdn' or 'value'")
            responses.append(
                {
                    "fqdn": fqdn,
                    "status": "error",
                    "message": "Missing required fields 'fqdn' or 'value'",
                }
            )
            dns_requests_total.labels(operation=operation, result="error").inc()
            return responses

        try:
            managed_zone = self._parse_fqdn(fqdn)
            record_name = f"{fqdn}."
            project_id = self.settings.gcloud_project
            if not project_id:
                raise ValueError("gcloud_project is not configured")

            if operation == "add":
                response = self._create_txt_record(project_id, managed_zone, record_name, value)
                success_message = "TXT record added successfully"
            else:
                response = self._delete_txt_record(project_id, managed_zone, record_name, value)
                success_message = "TXT record removed successfully"

            responses.append(
                {
                    "fqdn": fqdn,
                    "status": "success",
                    "message": success_message,
                    "response": response,
                }
            )
            dns_requests_total.labels(operation=operation, result="success").inc()
        except ValueError as exc:
            logger.warning(str(exc))
            responses.append({"fqdn": fqdn, "status": "error", "message": str(exc)})
            dns_requests_total.labels(operation=operation, result="error").inc()
        except HttpError as exc:
            logger.error("Failed to %s TXT record for %s: %s", operation, fqdn, exc)
            action = "add" if operation == "add" else "remove"
            responses.append(
                {
                    "fqdn": fqdn,
                    "status": "error",
                    "message": f"Failed to {action} TXT record",
                }
            )
            dns_requests_total.labels(operation=operation, result="error").inc()
        except (RefreshError, TransportError, ssl.SSLError, OSError) as exc:
            logger.error(
                "Google API transport/auth failure while attempting to %s TXT record for %s: %s",
                operation,
                fqdn,
                exc,
            )
            action = "add" if operation == "add" else "remove"
            responses.append(
                {
                    "fqdn": fqdn,
                    "status": "error",
                    "message": f"Failed to {action} TXT record due to Google API connectivity/authentication issue",
                }
            )
            dns_requests_total.labels(operation=operation, result="error").inc()
        except Exception as exc:
            logger.exception("Unexpected error for %s", fqdn)
            responses.append(
                {
                    "fqdn": fqdn,
                    "status": "error",
                    "message": "An unexpected error occurred",
                }
            )
            dns_requests_total.labels(operation=operation, result="error").inc()

        return responses

    def _create_txt_record(
        self,
        project_id: str,
        managed_zone: str,
        record_name: str,
        txt_value: str,
    ):
        body = {
            "kind": "dns#resourceRecordSet",
            "name": record_name,
            "type": "TXT",
            "ttl": self.settings.ttl,
            "rrdatas": [f'"{txt_value}"'],
        }

        logger.debug("Attempting to add TXT record: %s", body)
        request = self.dns_service.resourceRecordSets().create(
            project=project_id,
            managedZone=managed_zone,
            body=body,
        )
        response = request.execute(num_retries=self.settings.dns_api_num_retries)
        logger.info("TXT record added: %s with value %s", record_name, txt_value)
        return response

    def _delete_txt_record(
        self,
        project_id: str,
        managed_zone: str,
        record_name: str,
        txt_value: str,
    ):
        body = {
            "kind": "dns#resourceRecordSet",
            "name": record_name,
            "type": "TXT",
            "ttl": self.settings.ttl,
            "rrdatas": [f'"{txt_value}"'],
        }

        logger.debug("Attempting to delete TXT record: %s", body)
        request = self.dns_service.changes().create(
            project=project_id,
            managedZone=managed_zone,
            body={
                "kind": "dns#change",
                "deletions": [body],
            },
        )
        response = request.execute(num_retries=self.settings.dns_api_num_retries)
        logger.info("TXT record removed: %s with value %s", record_name, txt_value)
        return response

    def _parse_fqdn(self, fqdn: str) -> str:
        logger.debug("Parsing FQDN: %s", fqdn)

        managed_zones = self.settings.managed_zones or {}
        if not fqdn.startswith("_acme-challenge."):
            raise ValueError(f"Invalid FQDN format: {fqdn}")

        stripped_fqdn = fqdn[len("_acme-challenge.") :]
        if stripped_fqdn in managed_zones.values():
            for zone_name, zone_domain in managed_zones.items():
                if stripped_fqdn == zone_domain:
                    return zone_name

        if stripped_fqdn.endswith("."):
            stripped_fqdn = stripped_fqdn[:-1]

        fqdn_parts = stripped_fqdn.split(".")

        for i in range(1, len(fqdn_parts)):
            possible_domain = ".".join(fqdn_parts[i:])
            for zone_name, zone_domain in managed_zones.items():
                if possible_domain == zone_domain:
                    return zone_name

        raise ValueError(f"No managed zone found for FQDN: {fqdn}")
