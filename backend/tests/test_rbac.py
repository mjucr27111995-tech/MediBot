"""Tests for RBAC role-to-collection access mapping."""

import pytest

from app.rbac import (
    ROLE_COLLECTIONS,
    COLLECTION_ACCESS_ROLES,
    SQL_RAG_ROLES,
    VALID_ROLES,
    get_accessible_collections,
    get_access_roles_for_collection,
    can_use_sql_rag,
)


class TestRoleCollections:
    """Verify role → collection mapping matches the assignment spec."""

    def test_should_grantDoctor_clinicalNursingGeneral(self) -> None:
        collections = get_accessible_collections("doctor")
        assert set(collections) == {"clinical", "nursing", "general"}

    def test_should_grantNurse_nursingGeneral(self) -> None:
        collections = get_accessible_collections("nurse")
        assert set(collections) == {"nursing", "general"}

    def test_should_grantBillingExec_billingGeneral(self) -> None:
        collections = get_accessible_collections("billing_executive")
        assert set(collections) == {"billing", "general"}

    def test_should_grantTechnician_equipmentGeneral(self) -> None:
        collections = get_accessible_collections("technician")
        assert set(collections) == {"equipment", "general"}

    def test_should_grantAdmin_allCollections(self) -> None:
        collections = get_accessible_collections("admin")
        assert set(collections) == {
            "clinical", "nursing", "billing", "equipment", "general"
        }

    def test_should_returnEmpty_withInvalidRole(self) -> None:
        collections = get_accessible_collections("hacker")
        assert collections == []

    def test_should_haveExactlyFiveRoles(self) -> None:
        assert len(VALID_ROLES) == 5
        assert set(VALID_ROLES) == {
            "doctor", "nurse", "billing_executive", "technician", "admin"
        }


class TestCollectionAccessRoles:
    """Verify collection → roles reverse mapping."""

    def test_should_grantGeneral_toAllRoles(self) -> None:
        roles = get_access_roles_for_collection("general")
        assert set(roles) == {
            "doctor", "nurse", "billing_executive", "technician", "admin"
        }

    def test_should_grantClinical_toDoctorAndAdmin(self) -> None:
        roles = get_access_roles_for_collection("clinical")
        assert set(roles) == {"doctor", "admin"}

    def test_should_grantNursing_toNurseDoctorAdmin(self) -> None:
        roles = get_access_roles_for_collection("nursing")
        assert set(roles) == {"nurse", "doctor", "admin"}

    def test_should_grantBilling_toBillingExecAndAdmin(self) -> None:
        roles = get_access_roles_for_collection("billing")
        assert set(roles) == {"billing_executive", "admin"}

    def test_should_grantEquipment_toTechnicianAndAdmin(self) -> None:
        roles = get_access_roles_for_collection("equipment")
        assert set(roles) == {"technician", "admin"}

    def test_should_returnEmpty_withInvalidCollection(self) -> None:
        roles = get_access_roles_for_collection("secret_docs")
        assert roles == []


class TestSQLRAGPermissions:
    """Verify SQL RAG is restricted to billing_executive and admin."""

    def test_should_allowSqlRag_forBillingExecutive(self) -> None:
        assert can_use_sql_rag("billing_executive") is True

    def test_should_allowSqlRag_forAdmin(self) -> None:
        assert can_use_sql_rag("admin") is True

    def test_should_denySqlRag_forDoctor(self) -> None:
        assert can_use_sql_rag("doctor") is False

    def test_should_denySqlRag_forNurse(self) -> None:
        assert can_use_sql_rag("nurse") is False

    def test_should_denySqlRag_forTechnician(self) -> None:
        assert can_use_sql_rag("technician") is False

    def test_should_denySqlRag_forInvalidRole(self) -> None:
        assert can_use_sql_rag("hacker") is False


class TestRBACConsistency:
    """Verify ROLE_COLLECTIONS and COLLECTION_ACCESS_ROLES are in sync."""

    def test_should_beConsistent_roleToCollectionAndReverse(self) -> None:
        for role, collections in ROLE_COLLECTIONS.items():
            for collection in collections:
                assert role in COLLECTION_ACCESS_ROLES[collection], (
                    f"Role '{role}' has '{collection}' but reverse map missing"
                )

        for collection, roles in COLLECTION_ACCESS_ROLES.items():
            for role in roles:
                assert collection in ROLE_COLLECTIONS[role], (
                    f"Collection '{collection}' has '{role}' but forward map missing"
                )
