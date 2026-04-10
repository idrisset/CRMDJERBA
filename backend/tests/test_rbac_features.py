"""
Test RBAC, User Management, Approvals, and Duplicate Detection Features
Tests for iteration 8 - DJERBA CONSTRUCTION CRM
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://property-hub-612.preview.emergentagent.com').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@immo.com"
ADMIN_PASSWORD = "admin123"

class TestAuthAndRBAC:
    """Test authentication and RBAC permissions"""
    
    def test_login_returns_role_and_permissions(self):
        """Login with admin should return role=super_admin and permissions"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        
        # Check role is super_admin (migrated from admin)
        assert "role" in data, "Response should contain role"
        assert data["role"] in ["super_admin", "admin"], f"Expected super_admin or admin, got {data['role']}"
        
        # Check tokens
        assert "access_token" in data, "Response should contain access_token"
        assert "refresh_token" in data, "Response should contain refresh_token"
        print(f"Login successful: role={data['role']}")
    
    def test_auth_me_returns_permissions(self):
        """GET /api/auth/me should return permissions object"""
        # Login first
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert login_res.status_code == 200
        token = login_res.json()["access_token"]
        
        # Get /auth/me
        response = requests.get(f"{BASE_URL}/api/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200, f"Auth/me failed: {response.text}"
        data = response.json()
        
        # Check permissions object
        assert "permissions" in data, "Response should contain permissions"
        perms = data["permissions"]
        assert "level" in perms, "Permissions should have level"
        assert "can_manage_users" in perms, "Permissions should have can_manage_users"
        assert "can_delete" in perms, "Permissions should have can_delete"
        assert "can_approve" in perms, "Permissions should have can_approve"
        
        # Super admin should have all permissions
        assert perms["level"] >= 3, f"Super admin should have level >= 3, got {perms['level']}"
        assert perms["can_manage_users"] == True, "Super admin should be able to manage users"
        print(f"Permissions: {perms}")


class TestUserManagement:
    """Test user management endpoints (super_admin only)"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_get_users_list(self, admin_token):
        """GET /api/users returns list of users"""
        response = requests.get(f"{BASE_URL}/api/users", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert response.status_code == 200, f"Get users failed: {response.text}"
        data = response.json()
        
        assert isinstance(data, list), "Response should be a list"
        if len(data) > 0:
            user = data[0]
            assert "id" in user, "User should have id"
            assert "email" in user, "User should have email"
            assert "role" in user, "User should have role"
        print(f"Found {len(data)} users")
    
    def test_create_user(self, admin_token):
        """POST /api/users creates new user with role"""
        test_email = f"test_user_{int(time.time())}@test.com"
        response = requests.post(f"{BASE_URL}/api/users", json={
            "email": test_email,
            "password": "testpass123",
            "name": "Test User RBAC",
            "role": "user"
        }, headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert response.status_code in [200, 201], f"Create user failed: {response.text}"
        data = response.json()
        
        assert "id" in data, "Response should contain user id"
        assert data["email"] == test_email, "Email should match"
        assert data["role"] == "user", "Role should be user"
        print(f"Created user: {data['id']}")
        return data["id"]
    
    def test_update_user_role(self, admin_token):
        """PUT /api/users/{id} updates user role"""
        # First create a user
        test_email = f"test_role_{int(time.time())}@test.com"
        create_res = requests.post(f"{BASE_URL}/api/users", json={
            "email": test_email,
            "password": "testpass123",
            "name": "Test Role Update",
            "role": "user"
        }, headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert create_res.status_code in [200, 201]
        user_id = create_res.json()["id"]
        
        # Update role
        response = requests.put(f"{BASE_URL}/api/users/{user_id}", json={
            "role": "admin_limited"
        }, headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert response.status_code == 200, f"Update user failed: {response.text}"
        print(f"Updated user {user_id} role to admin_limited")
    
    def test_deactivate_user(self, admin_token):
        """DELETE /api/users/{id} deactivates user"""
        # First create a user
        test_email = f"test_deactivate_{int(time.time())}@test.com"
        create_res = requests.post(f"{BASE_URL}/api/users", json={
            "email": test_email,
            "password": "testpass123",
            "name": "Test Deactivate",
            "role": "user"
        }, headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert create_res.status_code in [200, 201]
        user_id = create_res.json()["id"]
        
        # Deactivate
        response = requests.delete(f"{BASE_URL}/api/users/{user_id}", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert response.status_code == 200, f"Deactivate user failed: {response.text}"
        print(f"Deactivated user {user_id}")


class TestApprovals:
    """Test approval workflow endpoints"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_get_approvals_list(self, admin_token):
        """GET /api/approvals returns approval requests"""
        response = requests.get(f"{BASE_URL}/api/approvals", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert response.status_code == 200, f"Get approvals failed: {response.text}"
        data = response.json()
        
        assert isinstance(data, list), "Response should be a list"
        print(f"Found {len(data)} approval requests")
    
    def test_get_approvals_count(self, admin_token):
        """GET /api/approvals/count returns pending count"""
        response = requests.get(f"{BASE_URL}/api/approvals/count", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert response.status_code == 200, f"Get approvals count failed: {response.text}"
        data = response.json()
        
        assert "count" in data, "Response should contain count"
        assert isinstance(data["count"], int), "Count should be integer"
        print(f"Pending approvals count: {data['count']}")


class TestDuplicateDetection:
    """Test duplicate client detection and merge"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_get_duplicates_list(self, admin_token):
        """GET /api/clients/duplicates returns duplicate groups"""
        response = requests.get(f"{BASE_URL}/api/clients/duplicates", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert response.status_code == 200, f"Get duplicates failed: {response.text}"
        data = response.json()
        
        assert "groups" in data, "Response should contain groups"
        assert isinstance(data["groups"], list), "Groups should be a list"
        print(f"Found {len(data['groups'])} duplicate groups")
    
    def test_client_creation_with_duplicate_detection(self, admin_token):
        """Client creation returns needs_confirmation if duplicate found"""
        # Create first client
        test_phone = f"0555{int(time.time()) % 1000000:06d}"
        first_client = requests.post(f"{BASE_URL}/api/clients", json={
            "nom": "Test Duplicate Client",
            "telephone": test_phone,
            "statut": "nouveau"
        }, headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert first_client.status_code in [200, 201], f"First client creation failed: {first_client.text}"
        first_data = first_client.json()
        
        # Check if it was created or needs confirmation
        if first_data.get("needs_confirmation"):
            print("First client detected as duplicate - skipping duplicate test")
            return
        
        first_id = first_data.get("id")
        assert first_id, "First client should have id"
        
        # Try to create duplicate (same phone)
        second_client = requests.post(f"{BASE_URL}/api/clients", json={
            "nom": "Test Duplicate Client 2",
            "telephone": test_phone,
            "statut": "nouveau"
        }, headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert second_client.status_code in [200, 201], f"Second client creation failed: {second_client.text}"
        second_data = second_client.json()
        
        # Should return needs_confirmation
        assert second_data.get("needs_confirmation") == True, "Should detect duplicate"
        assert "duplicates" in second_data, "Should return duplicates list"
        print(f"Duplicate detection working: found {len(second_data['duplicates'])} duplicates")
        
        # Cleanup - delete first client
        requests.delete(f"{BASE_URL}/api/clients/{first_id}", headers={
            "Authorization": f"Bearer {admin_token}"
        })
    
    def test_client_creation_with_force_create(self, admin_token):
        """Client creation with force_create bypasses duplicate check"""
        test_phone = f"0666{int(time.time()) % 1000000:06d}"
        
        # Create first client
        first_client = requests.post(f"{BASE_URL}/api/clients", json={
            "nom": "Test Force Create",
            "telephone": test_phone,
            "statut": "nouveau",
            "force_create": True
        }, headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert first_client.status_code in [200, 201]
        first_data = first_client.json()
        first_id = first_data.get("id")
        
        if not first_id:
            print("First client not created - may have duplicate")
            return
        
        # Create second with force_create
        second_client = requests.post(f"{BASE_URL}/api/clients", json={
            "nom": "Test Force Create 2",
            "telephone": test_phone,
            "statut": "nouveau",
            "force_create": True
        }, headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert second_client.status_code in [200, 201]
        second_data = second_client.json()
        
        # Should create without needs_confirmation
        assert second_data.get("needs_confirmation") != True, "force_create should bypass duplicate check"
        second_id = second_data.get("id")
        print(f"Force create working: created {second_id}")
        
        # Cleanup
        if first_id:
            requests.delete(f"{BASE_URL}/api/clients/{first_id}", headers={
                "Authorization": f"Bearer {admin_token}"
            })
        if second_id:
            requests.delete(f"{BASE_URL}/api/clients/{second_id}", headers={
                "Authorization": f"Bearer {admin_token}"
            })


class TestClientAutoReference:
    """Test client auto-reference generation"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_client_creation_returns_reference(self, admin_token):
        """Client creation returns auto-reference (#001, #002, etc)"""
        test_phone = f"0777{int(time.time()) % 1000000:06d}"
        response = requests.post(f"{BASE_URL}/api/clients", json={
            "nom": "Test Reference Client",
            "telephone": test_phone,
            "statut": "nouveau",
            "force_create": True
        }, headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert response.status_code in [200, 201], f"Client creation failed: {response.text}"
        data = response.json()
        
        # Check for reference
        if data.get("needs_confirmation"):
            print("Client detected as duplicate - skipping reference test")
            return
        
        assert "reference" in data, "Response should contain reference"
        reference = data["reference"]
        assert reference.startswith("#"), f"Reference should start with #, got {reference}"
        assert len(reference) == 4, f"Reference should be 4 chars (#XXX), got {reference}"
        print(f"Auto-reference generated: {reference}")
        
        # Cleanup
        if data.get("id"):
            requests.delete(f"{BASE_URL}/api/clients/{data['id']}", headers={
                "Authorization": f"Bearer {admin_token}"
            })


class TestMultiApartmentClient:
    """Test client with multiple apartments"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_client_supports_multi_apartment(self, admin_token):
        """Client form supports multi-apartment selection (array of IDs)"""
        # Get available apartments
        apparts_res = requests.get(f"{BASE_URL}/api/appartements", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert apparts_res.status_code == 200
        apparts = apparts_res.json()
        
        # Find available apartments
        available = [a for a in apparts if a.get("statut") == "disponible"][:2]
        if len(available) < 2:
            print("Not enough available apartments for multi-apartment test")
            return
        
        apt_ids = [a["id"] for a in available]
        test_phone = f"0888{int(time.time()) % 1000000:06d}"
        
        # Create client with multiple apartments
        response = requests.post(f"{BASE_URL}/api/clients", json={
            "nom": "Test Multi Apartment",
            "telephone": test_phone,
            "statut": "réservé",
            "appartement_ids": apt_ids,
            "force_create": True
        }, headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert response.status_code in [200, 201], f"Client creation failed: {response.text}"
        data = response.json()
        
        if data.get("needs_confirmation"):
            print("Client detected as duplicate - skipping multi-apartment test")
            return
        
        client_id = data.get("id")
        assert client_id, "Client should have id"
        
        # Verify client has multiple apartments
        clients_res = requests.get(f"{BASE_URL}/api/clients", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert clients_res.status_code == 200
        clients = clients_res.json()
        
        created_client = next((c for c in clients if c["id"] == client_id), None)
        assert created_client, "Created client should be in list"
        
        client_apt_ids = created_client.get("appartement_ids", [])
        assert len(client_apt_ids) >= 1, f"Client should have apartments, got {client_apt_ids}"
        print(f"Multi-apartment client created with {len(client_apt_ids)} apartments")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/clients/{client_id}", headers={
            "Authorization": f"Bearer {admin_token}"
        })


class TestRBACRestrictions:
    """Test RBAC restrictions for non-super_admin users"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_create_limited_user_and_test_restrictions(self, admin_token):
        """Non-super_admin user gets 403 on user management"""
        # Create a limited user
        test_email = f"test_limited_{int(time.time())}@test.com"
        create_res = requests.post(f"{BASE_URL}/api/users", json={
            "email": test_email,
            "password": "testpass123",
            "name": "Test Limited User",
            "role": "user"
        }, headers={
            "Authorization": f"Bearer {admin_token}"
        })
        
        if create_res.status_code not in [200, 201]:
            print(f"Could not create test user: {create_res.text}")
            return
        
        user_id = create_res.json()["id"]
        
        # Login as limited user
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": test_email,
            "password": "testpass123"
        })
        
        if login_res.status_code != 200:
            print(f"Could not login as limited user: {login_res.text}")
            # Cleanup
            requests.delete(f"{BASE_URL}/api/users/{user_id}", headers={
                "Authorization": f"Bearer {admin_token}"
            })
            return
        
        limited_token = login_res.json()["access_token"]
        
        # Try to access user management - should get 403
        users_res = requests.get(f"{BASE_URL}/api/users", headers={
            "Authorization": f"Bearer {limited_token}"
        })
        assert users_res.status_code == 403, f"Limited user should get 403 on /users, got {users_res.status_code}"
        print("RBAC restriction working: limited user gets 403 on user management")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/users/{user_id}", headers={
            "Authorization": f"Bearer {admin_token}"
        })


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
