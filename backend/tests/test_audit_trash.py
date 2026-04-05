"""
Test suite for EDIMCO CRM Audit Log and Trash (Soft Delete) System
Tests: audit logging, soft delete, restore, permanent delete (admin only)
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://property-hub-612.preview.emergentagent.com').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@immo.com"
ADMIN_PASSWORD = "admin123"

# Non-admin user for permission tests
NON_ADMIN_EMAIL = "test_commercial@immo.com"
NON_ADMIN_PASSWORD = "test123"


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    assert response.status_code == 200, f"Admin login failed: {response.text}"
    data = response.json()
    assert "access_token" in data, "No access_token in login response"
    return data["access_token"]


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    """Headers with admin auth token"""
    return {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json"
    }


@pytest.fixture(scope="module")
def non_admin_token():
    """Create and get non-admin user token for permission tests"""
    # First try to login
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": NON_ADMIN_EMAIL,
        "password": NON_ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json()["access_token"]
    
    # If login fails, register the user
    response = requests.post(f"{BASE_URL}/api/auth/register", json={
        "email": NON_ADMIN_EMAIL,
        "password": NON_ADMIN_PASSWORD,
        "name": "Test Commercial",
        "role": "commercial"
    })
    if response.status_code == 200:
        return response.json()["access_token"]
    
    # Try login again after registration
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": NON_ADMIN_EMAIL,
        "password": NON_ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json()["access_token"]
    
    pytest.skip("Could not create non-admin user for permission tests")


@pytest.fixture(scope="module")
def non_admin_headers(non_admin_token):
    """Headers with non-admin auth token"""
    return {
        "Authorization": f"Bearer {non_admin_token}",
        "Content-Type": "application/json"
    }


class TestLoginAuditLog:
    """Test that login action is logged in audit_logs"""
    
    def test_login_creates_audit_log(self, admin_headers):
        """POST /api/auth/login should log a LOGIN action"""
        # Login again to create a fresh audit log entry
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        # Small delay to ensure audit log is written
        time.sleep(0.5)
        
        # Check audit logs for LOGIN action
        response = requests.get(
            f"{BASE_URL}/api/audit-logs?action=LOGIN&limit=5",
            headers=admin_headers
        )
        assert response.status_code == 200, f"Audit logs fetch failed: {response.text}"
        logs = response.json()
        
        # Verify LOGIN action exists
        login_logs = [log for log in logs if log.get("action") == "LOGIN"]
        assert len(login_logs) > 0, "No LOGIN audit log found"
        
        # Verify log structure
        latest_login = login_logs[0]
        assert latest_login.get("entity_type") == "session", f"Expected entity_type 'session', got {latest_login.get('entity_type')}"
        assert latest_login.get("user_name"), "user_name should be present"
        print(f"✓ LOGIN audit log verified: {latest_login.get('user_name')} at {latest_login.get('timestamp')}")


class TestClientAuditLog:
    """Test audit logging for client CRUD operations"""
    
    @pytest.fixture
    def test_client_id(self, admin_headers):
        """Create a test client and return its ID"""
        client_data = {
            "nom": "TEST_AuditClient",
            "telephone": "0555123456",
            "email": "audit_test@example.com",
            "statut": "nouveau"
        }
        response = requests.post(f"{BASE_URL}/api/clients", json=client_data, headers=admin_headers)
        assert response.status_code == 200, f"Client creation failed: {response.text}"
        client_id = response.json().get("id")
        yield client_id
        # Cleanup: try to permanently delete if in trash, or soft delete first
        try:
            requests.delete(f"{BASE_URL}/api/clients/{client_id}", headers=admin_headers)
            requests.delete(f"{BASE_URL}/api/trash/client/{client_id}/permanent", headers=admin_headers)
        except:
            pass
    
    def test_create_client_logs_audit(self, admin_headers):
        """POST /api/clients should log CREATE action"""
        client_data = {
            "nom": "TEST_CreateAuditClient",
            "telephone": "0555111222",
            "statut": "nouveau"
        }
        response = requests.post(f"{BASE_URL}/api/clients", json=client_data, headers=admin_headers)
        assert response.status_code == 200, f"Client creation failed: {response.text}"
        client_id = response.json().get("id")
        
        time.sleep(0.5)
        
        # Check audit logs
        response = requests.get(
            f"{BASE_URL}/api/audit-logs?action=CREATE&entity_type=client&limit=10",
            headers=admin_headers
        )
        assert response.status_code == 200
        logs = response.json()
        
        # Find the log for our client
        create_logs = [log for log in logs if log.get("entity_name") == "TEST_CreateAuditClient"]
        assert len(create_logs) > 0, "CREATE audit log not found for client"
        
        log = create_logs[0]
        assert log.get("action") == "CREATE"
        assert log.get("entity_type") == "client"
        assert log.get("new_values") is not None, "new_values should be present for CREATE"
        print(f"✓ CREATE client audit log verified: {log.get('entity_name')}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/clients/{client_id}", headers=admin_headers)
        requests.delete(f"{BASE_URL}/api/trash/client/{client_id}/permanent", headers=admin_headers)
    
    def test_update_client_logs_audit_with_old_new_values(self, admin_headers, test_client_id):
        """PUT /api/clients/{id} should log UPDATE with old/new values"""
        # Update the client
        update_data = {"nom": "TEST_UpdatedAuditClient", "statut": "intéressé"}
        response = requests.put(
            f"{BASE_URL}/api/clients/{test_client_id}",
            json=update_data,
            headers=admin_headers
        )
        assert response.status_code == 200, f"Client update failed: {response.text}"
        
        time.sleep(0.5)
        
        # Check audit logs
        response = requests.get(
            f"{BASE_URL}/api/audit-logs?action=UPDATE&entity_type=client&limit=10",
            headers=admin_headers
        )
        assert response.status_code == 200
        logs = response.json()
        
        # Find the log for our client
        update_logs = [log for log in logs if log.get("entity_id") == test_client_id]
        assert len(update_logs) > 0, "UPDATE audit log not found for client"
        
        log = update_logs[0]
        assert log.get("action") == "UPDATE"
        assert log.get("old_values") is not None, "old_values should be present for UPDATE"
        assert log.get("new_values") is not None, "new_values should be present for UPDATE"
        print(f"✓ UPDATE client audit log verified with old_values: {log.get('old_values')}")


class TestSoftDelete:
    """Test soft delete functionality"""
    
    def test_delete_client_soft_deletes(self, admin_headers):
        """DELETE /api/clients/{id} should soft-delete (set deleted_at) instead of removing"""
        # Create a client
        client_data = {"nom": "TEST_SoftDeleteClient", "telephone": "0555333444"}
        response = requests.post(f"{BASE_URL}/api/clients", json=client_data, headers=admin_headers)
        assert response.status_code == 200
        client_id = response.json().get("id")
        
        # Delete the client (soft delete)
        response = requests.delete(f"{BASE_URL}/api/clients/{client_id}", headers=admin_headers)
        assert response.status_code == 200, f"Soft delete failed: {response.text}"
        assert "corbeille" in response.json().get("message", "").lower(), "Response should mention corbeille"
        
        time.sleep(0.5)
        
        # Verify client is NOT in regular clients list
        response = requests.get(f"{BASE_URL}/api/clients", headers=admin_headers)
        assert response.status_code == 200
        clients = response.json()
        client_ids = [c.get("id") for c in clients]
        assert client_id not in client_ids, "Soft-deleted client should not appear in GET /api/clients"
        
        # Verify DELETE action was logged
        response = requests.get(
            f"{BASE_URL}/api/audit-logs?action=DELETE&entity_type=client&limit=10",
            headers=admin_headers
        )
        assert response.status_code == 200
        logs = response.json()
        delete_logs = [log for log in logs if log.get("entity_id") == client_id]
        assert len(delete_logs) > 0, "DELETE audit log not found"
        print(f"✓ Soft delete verified: client {client_id} moved to trash")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/trash/client/{client_id}/permanent", headers=admin_headers)
    
    def test_get_clients_excludes_soft_deleted(self, admin_headers):
        """GET /api/clients should exclude soft-deleted clients"""
        # Create and soft-delete a client
        client_data = {"nom": "TEST_ExcludedClient", "telephone": "0555444555"}
        response = requests.post(f"{BASE_URL}/api/clients", json=client_data, headers=admin_headers)
        client_id = response.json().get("id")
        
        # Soft delete
        requests.delete(f"{BASE_URL}/api/clients/{client_id}", headers=admin_headers)
        
        # Verify excluded from list
        response = requests.get(f"{BASE_URL}/api/clients", headers=admin_headers)
        clients = response.json()
        client_ids = [c.get("id") for c in clients]
        assert client_id not in client_ids, "Soft-deleted client should be excluded"
        print("✓ GET /api/clients correctly excludes soft-deleted clients")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/trash/client/{client_id}/permanent", headers=admin_headers)


class TestTrashEndpoints:
    """Test trash/corbeille endpoints"""
    
    def test_get_trash_returns_soft_deleted_items(self, admin_headers):
        """GET /api/trash should return all soft-deleted items"""
        # Create and soft-delete a client
        client_data = {"nom": "TEST_TrashClient", "telephone": "0555666777"}
        response = requests.post(f"{BASE_URL}/api/clients", json=client_data, headers=admin_headers)
        client_id = response.json().get("id")
        requests.delete(f"{BASE_URL}/api/clients/{client_id}", headers=admin_headers)
        
        time.sleep(0.5)
        
        # Get trash
        response = requests.get(f"{BASE_URL}/api/trash", headers=admin_headers)
        assert response.status_code == 200, f"Get trash failed: {response.text}"
        trash_items = response.json()
        
        # Verify structure
        assert isinstance(trash_items, list), "Trash should return a list"
        
        # Find our client in trash
        our_item = next((item for item in trash_items if item.get("id") == client_id), None)
        assert our_item is not None, "Soft-deleted client should appear in trash"
        assert our_item.get("entity_type") == "client"
        assert our_item.get("entity_name") == "TEST_TrashClient"
        assert our_item.get("deleted_at") is not None
        assert our_item.get("deleted_by_name") is not None
        print(f"✓ GET /api/trash returns soft-deleted items with correct structure")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/trash/client/{client_id}/permanent", headers=admin_headers)
    
    def test_restore_from_trash(self, admin_headers):
        """POST /api/trash/client/{id}/restore should restore a soft-deleted client"""
        # Create and soft-delete a client
        client_data = {"nom": "TEST_RestoreClient", "telephone": "0555888999"}
        response = requests.post(f"{BASE_URL}/api/clients", json=client_data, headers=admin_headers)
        client_id = response.json().get("id")
        requests.delete(f"{BASE_URL}/api/clients/{client_id}", headers=admin_headers)
        
        # Restore
        response = requests.post(
            f"{BASE_URL}/api/trash/client/{client_id}/restore",
            headers=admin_headers
        )
        assert response.status_code == 200, f"Restore failed: {response.text}"
        
        time.sleep(0.5)
        
        # Verify client is back in regular list
        response = requests.get(f"{BASE_URL}/api/clients", headers=admin_headers)
        clients = response.json()
        client_ids = [c.get("id") for c in clients]
        assert client_id in client_ids, "Restored client should appear in GET /api/clients"
        
        # Verify RESTORE action was logged
        response = requests.get(
            f"{BASE_URL}/api/audit-logs?action=RESTORE&limit=10",
            headers=admin_headers
        )
        logs = response.json()
        restore_logs = [log for log in logs if log.get("entity_id") == client_id]
        assert len(restore_logs) > 0, "RESTORE audit log not found"
        print(f"✓ Restore from trash verified: client {client_id} restored and logged")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/clients/{client_id}", headers=admin_headers)
        requests.delete(f"{BASE_URL}/api/trash/client/{client_id}/permanent", headers=admin_headers)


class TestPermanentDelete:
    """Test permanent delete functionality (admin only)"""
    
    def test_permanent_delete_admin_success(self, admin_headers):
        """DELETE /api/trash/client/{id}/permanent should permanently delete (admin)"""
        # Create and soft-delete a client
        client_data = {"nom": "TEST_PermanentDeleteClient", "telephone": "0555000111"}
        response = requests.post(f"{BASE_URL}/api/clients", json=client_data, headers=admin_headers)
        client_id = response.json().get("id")
        requests.delete(f"{BASE_URL}/api/clients/{client_id}", headers=admin_headers)
        
        # Permanent delete
        response = requests.delete(
            f"{BASE_URL}/api/trash/client/{client_id}/permanent",
            headers=admin_headers
        )
        assert response.status_code == 200, f"Permanent delete failed: {response.text}"
        
        time.sleep(0.5)
        
        # Verify client is NOT in trash anymore
        response = requests.get(f"{BASE_URL}/api/trash", headers=admin_headers)
        trash_items = response.json()
        trash_ids = [item.get("id") for item in trash_items]
        assert client_id not in trash_ids, "Permanently deleted client should not be in trash"
        
        # Verify PERMANENT_DELETE action was logged
        response = requests.get(
            f"{BASE_URL}/api/audit-logs?action=PERMANENT_DELETE&limit=10",
            headers=admin_headers
        )
        logs = response.json()
        perm_delete_logs = [log for log in logs if log.get("entity_id") == client_id]
        assert len(perm_delete_logs) > 0, "PERMANENT_DELETE audit log not found"
        print(f"✓ Permanent delete verified: client {client_id} removed and logged")
    
    def test_permanent_delete_non_admin_forbidden(self, non_admin_headers, admin_headers):
        """DELETE /api/trash/client/{id}/permanent should return 403 for non-admin"""
        # Create and soft-delete a client (as admin)
        client_data = {"nom": "TEST_ForbiddenDeleteClient", "telephone": "0555222333"}
        response = requests.post(f"{BASE_URL}/api/clients", json=client_data, headers=admin_headers)
        client_id = response.json().get("id")
        requests.delete(f"{BASE_URL}/api/clients/{client_id}", headers=admin_headers)
        
        # Try permanent delete as non-admin
        response = requests.delete(
            f"{BASE_URL}/api/trash/client/{client_id}/permanent",
            headers=non_admin_headers
        )
        assert response.status_code == 403, f"Expected 403 for non-admin, got {response.status_code}"
        print("✓ Permanent delete correctly returns 403 for non-admin users")
        
        # Cleanup (as admin)
        requests.delete(f"{BASE_URL}/api/trash/client/{client_id}/permanent", headers=admin_headers)


class TestProspectAuditAndTrash:
    """Test audit and trash for prospects"""
    
    def test_create_prospect_logs_audit(self, admin_headers):
        """POST /api/prospects should log CREATE action"""
        prospect_data = {
            "nom": "TEST_AuditProspect",
            "telephone": "0666111222",
            "ville": "Alger",
            "source": "foire"
        }
        response = requests.post(f"{BASE_URL}/api/prospects", json=prospect_data, headers=admin_headers)
        assert response.status_code == 200, f"Prospect creation failed: {response.text}"
        prospect_id = response.json().get("id")
        
        time.sleep(0.5)
        
        # Check audit logs
        response = requests.get(
            f"{BASE_URL}/api/audit-logs?action=CREATE&entity_type=prospect&limit=10",
            headers=admin_headers
        )
        logs = response.json()
        create_logs = [log for log in logs if log.get("entity_name") == "TEST_AuditProspect"]
        assert len(create_logs) > 0, "CREATE audit log not found for prospect"
        print(f"✓ CREATE prospect audit log verified")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/prospects/{prospect_id}", headers=admin_headers)
        requests.delete(f"{BASE_URL}/api/trash/prospect/{prospect_id}/permanent", headers=admin_headers)
    
    def test_delete_prospect_soft_deletes_and_logs(self, admin_headers):
        """DELETE /api/prospects/{id} should soft-delete and log"""
        # Create prospect
        prospect_data = {"nom": "TEST_SoftDeleteProspect", "telephone": "0666333444"}
        response = requests.post(f"{BASE_URL}/api/prospects", json=prospect_data, headers=admin_headers)
        prospect_id = response.json().get("id")
        
        # Soft delete
        response = requests.delete(f"{BASE_URL}/api/prospects/{prospect_id}", headers=admin_headers)
        assert response.status_code == 200
        
        time.sleep(0.5)
        
        # Verify in trash
        response = requests.get(f"{BASE_URL}/api/trash", headers=admin_headers)
        trash_items = response.json()
        prospect_in_trash = next((item for item in trash_items if item.get("id") == prospect_id), None)
        assert prospect_in_trash is not None, "Soft-deleted prospect should be in trash"
        assert prospect_in_trash.get("entity_type") == "prospect"
        
        # Verify DELETE logged
        response = requests.get(
            f"{BASE_URL}/api/audit-logs?action=DELETE&entity_type=prospect&limit=10",
            headers=admin_headers
        )
        logs = response.json()
        delete_logs = [log for log in logs if log.get("entity_id") == prospect_id]
        assert len(delete_logs) > 0, "DELETE audit log not found for prospect"
        print(f"✓ Prospect soft delete and audit log verified")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/trash/prospect/{prospect_id}/permanent", headers=admin_headers)
    
    def test_restore_prospect_from_trash(self, admin_headers):
        """POST /api/trash/prospect/{id}/restore should restore prospect"""
        # Create and soft-delete
        prospect_data = {"nom": "TEST_RestoreProspect", "telephone": "0666555666"}
        response = requests.post(f"{BASE_URL}/api/prospects", json=prospect_data, headers=admin_headers)
        prospect_id = response.json().get("id")
        requests.delete(f"{BASE_URL}/api/prospects/{prospect_id}", headers=admin_headers)
        
        # Restore
        response = requests.post(
            f"{BASE_URL}/api/trash/prospect/{prospect_id}/restore",
            headers=admin_headers
        )
        assert response.status_code == 200
        
        # Verify back in list
        response = requests.get(f"{BASE_URL}/api/prospects", headers=admin_headers)
        prospects = response.json()
        prospect_ids = [p.get("id") for p in prospects]
        assert prospect_id in prospect_ids, "Restored prospect should be in list"
        print(f"✓ Prospect restore verified")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/prospects/{prospect_id}", headers=admin_headers)
        requests.delete(f"{BASE_URL}/api/trash/prospect/{prospect_id}/permanent", headers=admin_headers)


class TestAuditLogFilters:
    """Test audit log filtering functionality"""
    
    def test_filter_by_action(self, admin_headers):
        """GET /api/audit-logs?action=LOGIN should filter by action"""
        response = requests.get(
            f"{BASE_URL}/api/audit-logs?action=LOGIN",
            headers=admin_headers
        )
        assert response.status_code == 200
        logs = response.json()
        
        # All logs should have action=LOGIN
        for log in logs:
            assert log.get("action") == "LOGIN", f"Expected action LOGIN, got {log.get('action')}"
        print(f"✓ Filter by action works: {len(logs)} LOGIN logs found")
    
    def test_filter_by_entity_type(self, admin_headers):
        """GET /api/audit-logs?entity_type=client should filter by entity type"""
        response = requests.get(
            f"{BASE_URL}/api/audit-logs?entity_type=client",
            headers=admin_headers
        )
        assert response.status_code == 200
        logs = response.json()
        
        # All logs should have entity_type=client
        for log in logs:
            assert log.get("entity_type") == "client", f"Expected entity_type client, got {log.get('entity_type')}"
        print(f"✓ Filter by entity_type works: {len(logs)} client logs found")
    
    def test_filter_by_search(self, admin_headers):
        """GET /api/audit-logs?search=TEST should filter by search term"""
        response = requests.get(
            f"{BASE_URL}/api/audit-logs?search=TEST",
            headers=admin_headers
        )
        assert response.status_code == 200
        logs = response.json()
        
        # All logs should contain TEST in entity_name or user_name
        for log in logs:
            entity_name = log.get("entity_name", "").upper()
            user_name = log.get("user_name", "").upper()
            assert "TEST" in entity_name or "TEST" in user_name, f"Search filter not working for log: {log}"
        print(f"✓ Search filter works: {len(logs)} logs matching 'TEST'")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
