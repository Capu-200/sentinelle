"""
Helpers to expose consistent public transaction statuses to clients.
"""
from typing import Optional

PUBLIC_STATUS_MAP = {
    "PENDING": "ANALYZING",
    "ANALYZING": "ANALYZING",
    "VALIDATED": "VALIDATED",
    "APPROVED": "VALIDATED",
    "REVIEW": "SUSPECT",
    "SUSPECT": "SUSPECT",
    "REJECTED": "REJECTED",
    "FAILED": "REJECTED",
}

DEFAULT_PUBLIC_STATUS = "ANALYZING"


def map_kyc_status_to_public(kyc_status: Optional[str]) -> str:
    """Return the public status a client should see for a transaction."""
    if not kyc_status:
        return DEFAULT_PUBLIC_STATUS
    return PUBLIC_STATUS_MAP.get(kyc_status.upper(), DEFAULT_PUBLIC_STATUS)
