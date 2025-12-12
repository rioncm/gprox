"""
Prometheus metrics definitions.
"""

from prometheus_client import Counter

dns_requests_total = Counter(
    "gprox_dns_requests_total",
    "Counts DNS TXT record operations processed by GPROX.",
    ("operation", "result"),
)
