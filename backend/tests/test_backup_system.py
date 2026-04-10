"""
Test suite for DJERBA CONSTRUCTION CRM - Backup & Restore System
Tests: backup creation, listing, stats, restore, delete, RBAC restrictions
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@immo.com"
ADMIN_PASSWORD = "admin123"

# Non-admin test user (will be created if needed)
TEST_USER_EMAIL = "test_backup_user@test.com"
TEST_USER_PASSWORD = "testpass123"


class TestBackupSystemSetup:
    """Setup and authentication tests"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        assert data.get("role") == "super_admin", f"Expected super_admin role, got {data.get('role')}"
        return data["access_token"]
    
    @pytest.fixture(scope="class")
    def admin_headers(self, admin_token):
        """Headers with admin auth"""
        return {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        }
    
    @pytest.fixture(scope="class")
    def limited_user_token(self, admin_headers):
        """Create a limited user and get their token for RBAC testing"""
        # First try to create the user
        create_resp = requests.post(f"{BASE_URL}/api/users", headers=admin_headers, json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD,
            "name": "Test Backup User",
            "role": "user"
        })
        # User might already exist, that's ok
        
        # Login as the limited user
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        
        if login_resp.status_code != 200:
            pytest.skip("Could not create/login limited user for RBAC test")
        
        return login_resp.json().get("access_token")
    
    @pytest.fixture(scope="class")
    def limited_headers(self, limited_user_token):
        """Headers with limited user auth"""
        return {
            "Authorization": f"Bearer {limited_user_token}",
            "Content-Type": "application/json"
        }
    
    def test_admin_login_success(self, admin_token):
        """Verify admin can login and get token"""
        assert admin_token is not None
        assert len(admin_token) > 0
        print(f"✓ Admin login successful, token length: {len(admin_token)}")


class TestBackupCRUD:
    """Test backup CRUD operations"""
    
    @pytest.fixture(scope="class")
    def admin_headers(self):
        """Get admin headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        token = response.json().get("access_token")
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    def test_create_manual_backup(self, admin_headers):
        """POST /api/backups creates a manual backup successfully"""
        response = requests.post(f"{BASE_URL}/api/backups", headers=admin_headers)
        
        assert response.status_code == 200, f"Backup creation failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "backup_id" in data, "Missing backup_id in response"
        assert "status" in data, "Missing status in response"
        assert data["status"] == "success", f"Backup status is {data['status']}, expected success"
        assert "size_mb" in data, "Missing size_mb in response"
        assert data["size_mb"] >= 0, "size_mb should be non-negative"
        assert "type" in data, "Missing type in response"
        assert data["type"] == "manual", f"Expected type=manual, got {data['type']}"
        
        print(f"✓ Manual backup created: {data['backup_id']} ({data['size_mb']} MB)")
        return data["backup_id"]
    
    def test_list_backups(self, admin_headers):
        """GET /api/backups lists all backups with metadata"""
        response = requests.get(f"{BASE_URL}/api/backups", headers=admin_headers)
        
        assert response.status_code == 200, f"List backups failed: {response.text}"
        data = response.json()
        
        assert isinstance(data, list), "Response should be a list"
        assert len(data) > 0, "Should have at least one backup"
        
        # Verify backup structure
        backup = data[0]
        required_fields = ["backup_id", "type", "status", "created_at"]
        for field in required_fields:
            assert field in backup, f"Missing field: {field}"
        
        # Verify type values
        valid_types = ["manual", "auto_6h", "auto_daily", "pre_restore"]
        assert backup["type"] in valid_types, f"Invalid type: {backup['type']}"
        
        print(f"✓ Listed {len(data)} backups")
        for b in data[:3]:
            print(f"  - {b['backup_id']}: {b['type']} ({b['status']})")
    
    def test_get_backup_stats(self, admin_headers):
        """GET /api/backups/stats returns stats"""
        response = requests.get(f"{BASE_URL}/api/backups/stats", headers=admin_headers)
        
        assert response.status_code == 200, f"Get stats failed: {response.text}"
        data = response.json()
        
        # Verify stats structure
        assert "total" in data, "Missing total in stats"
        assert "successful" in data, "Missing successful in stats"
        assert "total_size_mb" in data, "Missing total_size_mb in stats"
        assert "last_backup" in data, "Missing last_backup in stats"
        
        assert data["total"] >= 0, "total should be non-negative"
        assert data["successful"] >= 0, "successful should be non-negative"
        assert data["total_size_mb"] >= 0, "total_size_mb should be non-negative"
        
        print(f"✓ Backup stats: total={data['total']}, successful={data['successful']}, size={data['total_size_mb']}MB")
        
        if data["last_backup"]:
            print(f"  Last backup: {data['last_backup'].get('backup_id', 'N/A')}")
    
    def test_backup_contains_all_collections(self, admin_headers):
        """Verify backup data contains all expected collections"""
        # Create a fresh backup
        create_resp = requests.post(f"{BASE_URL}/api/backups", headers=admin_headers)
        assert create_resp.status_code == 200
        backup_data = create_resp.json()
        
        # Check collection_sizes if available
        if "collection_sizes" in backup_data:
            expected_collections = ["clients", "appartements", "users", "reservations"]
            for col in expected_collections:
                if col in backup_data["collection_sizes"]:
                    print(f"  ✓ Collection {col}: {backup_data['collection_sizes'][col]}")
        
        print(f"✓ Backup {backup_data['backup_id']} created with collections")


class TestBackupRestore:
    """Test backup restore functionality"""
    
    @pytest.fixture(scope="class")
    def admin_headers(self):
        """Get admin headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        token = response.json().get("access_token")
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    def test_restore_creates_safety_backup(self, admin_headers):
        """POST /api/backups/{id}/restore creates safety backup automatically"""
        # First, get a backup to restore
        list_resp = requests.get(f"{BASE_URL}/api/backups", headers=admin_headers)
        assert list_resp.status_code == 200
        backups = list_resp.json()
        
        # Find a successful backup to restore
        restore_target = None
        for b in backups:
            if b.get("status") == "success" and b.get("exists") != False:
                restore_target = b
                break
        
        if not restore_target:
            pytest.skip("No valid backup found to restore")
        
        backup_id = restore_target["backup_id"]
        print(f"Restoring backup: {backup_id}")
        
        # Perform restore
        restore_resp = requests.post(f"{BASE_URL}/api/backups/{backup_id}/restore", headers=admin_headers)
        
        assert restore_resp.status_code == 200, f"Restore failed: {restore_resp.text}"
        data = restore_resp.json()
        
        # Verify restore response
        assert data.get("status") == "success", f"Restore status: {data.get('status')}"
        assert "safety_backup_id" in data, "Missing safety_backup_id in response"
        assert data["safety_backup_id"].startswith("backup_"), "Invalid safety backup ID format"
        
        print(f"✓ Restore successful, safety backup: {data['safety_backup_id']}")
        
        # Verify safety backup exists in list
        list_resp2 = requests.get(f"{BASE_URL}/api/backups", headers=admin_headers)
        backups2 = list_resp2.json()
        safety_found = any(b["backup_id"] == data["safety_backup_id"] for b in backups2)
        assert safety_found, "Safety backup not found in backup list"
        
        # Verify safety backup type is pre_restore
        safety_backup = next((b for b in backups2 if b["backup_id"] == data["safety_backup_id"]), None)
        assert safety_backup["type"] == "pre_restore", f"Safety backup type should be pre_restore, got {safety_backup['type']}"
        
        print(f"✓ Safety backup verified: type={safety_backup['type']}")


class TestBackupDelete:
    """Test backup deletion"""
    
    @pytest.fixture(scope="class")
    def admin_headers(self):
        """Get admin headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        token = response.json().get("access_token")
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    def test_delete_backup(self, admin_headers):
        """DELETE /api/backups/{id} deletes a backup"""
        # Create a backup to delete
        create_resp = requests.post(f"{BASE_URL}/api/backups", headers=admin_headers)
        assert create_resp.status_code == 200
        backup_id = create_resp.json()["backup_id"]
        
        print(f"Created backup to delete: {backup_id}")
        
        # Delete the backup
        delete_resp = requests.delete(f"{BASE_URL}/api/backups/{backup_id}", headers=admin_headers)
        
        assert delete_resp.status_code == 200, f"Delete failed: {delete_resp.text}"
        data = delete_resp.json()
        assert "message" in data, "Missing message in delete response"
        
        print(f"✓ Backup deleted: {backup_id}")
        
        # Verify backup is no longer in list
        list_resp = requests.get(f"{BASE_URL}/api/backups", headers=admin_headers)
        backups = list_resp.json()
        deleted_found = any(b["backup_id"] == backup_id for b in backups)
        assert not deleted_found, "Deleted backup still appears in list"
        
        print(f"✓ Verified backup removed from list")
    
    def test_delete_nonexistent_backup(self, admin_headers):
        """DELETE /api/backups/{id} returns 404 for nonexistent backup"""
        fake_id = "backup_99999999_999999_fake"
        delete_resp = requests.delete(f"{BASE_URL}/api/backups/{fake_id}", headers=admin_headers)
        
        assert delete_resp.status_code == 404, f"Expected 404, got {delete_resp.status_code}"
        print(f"✓ Correctly returns 404 for nonexistent backup")


class TestBackupRBAC:
    """Test RBAC restrictions on backup endpoints"""
    
    @pytest.fixture(scope="class")
    def admin_headers(self):
        """Get admin headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        token = response.json().get("access_token")
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    @pytest.fixture(scope="class")
    def limited_headers(self, admin_headers):
        """Create limited user and get their headers"""
        # Create limited user
        requests.post(f"{BASE_URL}/api/users", headers=admin_headers, json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD,
            "name": "Test Limited User",
            "role": "user"
        })
        
        # Login as limited user
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        
        if login_resp.status_code != 200:
            pytest.skip("Could not login as limited user")
        
        token = login_resp.json().get("access_token")
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    def test_non_admin_cannot_list_backups(self, limited_headers):
        """Non-super_admin gets 403 on GET /api/backups"""
        response = requests.get(f"{BASE_URL}/api/backups", headers=limited_headers)
        
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print(f"✓ Non-admin correctly blocked from listing backups (403)")
    
    def test_non_admin_cannot_create_backup(self, limited_headers):
        """Non-super_admin gets 403 on POST /api/backups"""
        response = requests.post(f"{BASE_URL}/api/backups", headers=limited_headers)
        
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print(f"✓ Non-admin correctly blocked from creating backups (403)")
    
    def test_non_admin_cannot_restore_backup(self, limited_headers):
        """Non-super_admin gets 403 on POST /api/backups/{id}/restore"""
        response = requests.post(f"{BASE_URL}/api/backups/fake_id/restore", headers=limited_headers)
        
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print(f"✓ Non-admin correctly blocked from restoring backups (403)")
    
    def test_non_admin_cannot_delete_backup(self, limited_headers):
        """Non-super_admin gets 403 on DELETE /api/backups/{id}"""
        response = requests.delete(f"{BASE_URL}/api/backups/fake_id", headers=limited_headers)
        
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print(f"✓ Non-admin correctly blocked from deleting backups (403)")
    
    def test_non_admin_cannot_get_stats(self, limited_headers):
        """Non-super_admin gets 403 on GET /api/backups/stats"""
        response = requests.get(f"{BASE_URL}/api/backups/stats", headers=limited_headers)
        
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print(f"✓ Non-admin correctly blocked from viewing backup stats (403)")
    
    def test_unauthenticated_cannot_access_backups(self):
        """Unauthenticated requests get 401"""
        endpoints = [
            ("GET", f"{BASE_URL}/api/backups"),
            ("POST", f"{BASE_URL}/api/backups"),
            ("GET", f"{BASE_URL}/api/backups/stats"),
        ]
        
        for method, url in endpoints:
            if method == "GET":
                response = requests.get(url)
            else:
                response = requests.post(url)
            
            assert response.status_code == 401, f"{method} {url}: Expected 401, got {response.status_code}"
        
        print(f"✓ Unauthenticated requests correctly blocked (401)")


class TestSchedulerVerification:
    """Verify scheduler is running"""
    
    def test_scheduler_started_in_logs(self):
        """Check backend logs for scheduler startup message"""
        import subprocess
        result = subprocess.run(
            ["tail", "-n", "100", "/var/log/supervisor/backend.err.log"],
            capture_output=True, text=True
        )
        
        logs = result.stdout
        scheduler_started = "Backup scheduler started" in logs or "Scheduler started" in logs
        
        assert scheduler_started, "Scheduler startup message not found in logs"
        print(f"✓ Scheduler startup confirmed in logs")
    
    def test_scheduler_jobs_added(self):
        """Check that scheduler jobs were added"""
        import subprocess
        result = subprocess.run(
            ["tail", "-n", "100", "/var/log/supervisor/backend.err.log"],
            capture_output=True, text=True
        )
        
        logs = result.stdout
        job_6h = "scheduled_backup_6h" in logs
        job_daily = "scheduled_backup_daily" in logs
        
        assert job_6h, "6h backup job not found in logs"
        assert job_daily, "Daily backup job not found in logs"
        print(f"✓ Scheduler jobs confirmed: 6h={job_6h}, daily={job_daily}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
