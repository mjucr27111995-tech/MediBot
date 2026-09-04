"""RBAC definitions — role-to-collection access mapping."""

from typing import Dict, List

ROLE_COLLECTIONS: Dict[str, List[str]] = {
    "doctor": ["clinical", "nursing", "general"],
    "nurse": ["nursing", "general"],
    "billing_executive": ["billing", "general"],
    "technician": ["equipment", "general"],
    "admin": ["clinical", "nursing", "billing", "equipment", "general"],
}

COLLECTION_ACCESS_ROLES: Dict[str, List[str]] = {
    "general": ["doctor", "nurse", "billing_executive", "technician", "admin"],
    "clinical": ["doctor", "admin"],
    "nursing": ["nurse", "doctor", "admin"],
    "billing": ["billing_executive", "admin"],
    "equipment": ["technician", "admin"],
}

SQL_RAG_ROLES: List[str] = ["billing_executive", "admin"]

VALID_ROLES: List[str] = list(ROLE_COLLECTIONS.keys())


def get_accessible_collections(role: str) -> List[str]:
    """Return the list of document collections a role can access."""
    return ROLE_COLLECTIONS.get(role, [])


def get_access_roles_for_collection(collection: str) -> List[str]:
    """Return the roles that can access a given collection."""
    return COLLECTION_ACCESS_ROLES.get(collection, [])


def can_use_sql_rag(role: str) -> bool:
    """Check if a role is permitted to use SQL RAG."""
    return role in SQL_RAG_ROLES
