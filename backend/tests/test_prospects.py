"""
Test suite for Prospects (Big Data) feature - EDIMCO CRM
Tests CRUD operations, analytics, and export endpoints for prospects
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestProspectsCRUD:
    """Test Prospects CRUD operations"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@immo.com",
            "password": "admin123"
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        self.token = login_response.json().get("access_token")
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def test_get_prospects_list(self):
        """GET /api/prospects - List all prospects"""
        response = requests.get(f"{BASE_URL}/api/prospects", headers=self.headers)
        assert response.status_code == 200, f"Failed to get prospects: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"Found {len(data)} prospects in database")
        
        # Verify structure if prospects exist
        if len(data) > 0:
            prospect = data[0]
            assert "id" in prospect, "Prospect should have id"
            assert "nom" in prospect, "Prospect should have nom"
            assert "telephone" in prospect, "Prospect should have telephone"
            assert "ville" in prospect, "Prospect should have ville"
            assert "type_logement" in prospect, "Prospect should have type_logement"
            print(f"First prospect: {prospect['nom']} - {prospect['ville']}")
    
    def test_create_prospect(self):
        """POST /api/prospects - Create a new prospect"""
        prospect_data = {
            "nom": "TEST_Prospect_Ahmed",
            "telephone": "0555123456",
            "telephone2": "0666789012",
            "email": "test.ahmed@example.com",
            "ville": "Bejaia",
            "quartier": "Ihaddaden",
            "type_logement": "F3",
            "etage_souhaite": "3",
            "nombre_pieces": 3,
            "budget_min": 3000000,
            "budget_max": 5000000,
            "mode_paiement": "Crédit bancaire",
            "objectif": "Achat personnel",
            "situation_familiale": "Marié(e)",
            "notes": "Test prospect for automated testing",
            "source": "Foire"
        }
        
        response = requests.post(f"{BASE_URL}/api/prospects", json=prospect_data, headers=self.headers)
        assert response.status_code == 200, f"Failed to create prospect: {response.text}"
        
        created = response.json()
        assert "id" in created, "Created prospect should have id"
        assert created["nom"] == prospect_data["nom"], "Name should match"
        assert created["telephone"] == prospect_data["telephone"], "Phone should match"
        assert created["ville"] == prospect_data["ville"], "City should match"
        assert created["type_logement"] == prospect_data["type_logement"], "Housing type should match"
        assert created["budget_min"] == prospect_data["budget_min"], "Budget min should match"
        assert created["budget_max"] == prospect_data["budget_max"], "Budget max should match"
        
        print(f"Created prospect: {created['id']} - {created['nom']}")
        
        # Verify persistence with GET
        get_response = requests.get(f"{BASE_URL}/api/prospects", headers=self.headers)
        assert get_response.status_code == 200
        prospects = get_response.json()
        found = any(p["id"] == created["id"] for p in prospects)
        assert found, "Created prospect should be in list"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/prospects/{created['id']}", headers=self.headers)
    
    def test_create_prospect_minimal(self):
        """POST /api/prospects - Create prospect with minimal required fields"""
        prospect_data = {
            "nom": "TEST_Minimal_Prospect",
            "telephone": "0555999888"
        }
        
        response = requests.post(f"{BASE_URL}/api/prospects", json=prospect_data, headers=self.headers)
        assert response.status_code == 200, f"Failed to create minimal prospect: {response.text}"
        
        created = response.json()
        assert created["nom"] == prospect_data["nom"]
        assert created["telephone"] == prospect_data["telephone"]
        print(f"Created minimal prospect: {created['id']}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/prospects/{created['id']}", headers=self.headers)
    
    def test_update_prospect(self):
        """PUT /api/prospects/{id} - Update a prospect"""
        # First create a prospect
        create_data = {
            "nom": "TEST_Update_Prospect",
            "telephone": "0555111222",
            "ville": "Alger",
            "type_logement": "F2"
        }
        create_response = requests.post(f"{BASE_URL}/api/prospects", json=create_data, headers=self.headers)
        assert create_response.status_code == 200
        prospect_id = create_response.json()["id"]
        
        # Update the prospect
        update_data = {
            "nom": "TEST_Update_Prospect_Modified",
            "ville": "Oran",
            "type_logement": "F4",
            "budget_max": 8000000
        }
        update_response = requests.put(f"{BASE_URL}/api/prospects/{prospect_id}", json=update_data, headers=self.headers)
        assert update_response.status_code == 200, f"Failed to update prospect: {update_response.text}"
        
        updated = update_response.json()
        assert updated["nom"] == update_data["nom"], "Name should be updated"
        assert updated["ville"] == update_data["ville"], "City should be updated"
        assert updated["type_logement"] == update_data["type_logement"], "Type should be updated"
        
        # Verify persistence
        get_response = requests.get(f"{BASE_URL}/api/prospects", headers=self.headers)
        prospects = get_response.json()
        found_prospect = next((p for p in prospects if p["id"] == prospect_id), None)
        assert found_prospect is not None, "Updated prospect should exist"
        assert found_prospect["ville"] == "Oran", "City update should persist"
        
        print(f"Updated prospect: {prospect_id} - ville changed to Oran")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/prospects/{prospect_id}", headers=self.headers)
    
    def test_delete_prospect(self):
        """DELETE /api/prospects/{id} - Delete a prospect"""
        # First create a prospect
        create_data = {
            "nom": "TEST_Delete_Prospect",
            "telephone": "0555333444"
        }
        create_response = requests.post(f"{BASE_URL}/api/prospects", json=create_data, headers=self.headers)
        assert create_response.status_code == 200
        prospect_id = create_response.json()["id"]
        
        # Delete the prospect
        delete_response = requests.delete(f"{BASE_URL}/api/prospects/{prospect_id}", headers=self.headers)
        assert delete_response.status_code == 200, f"Failed to delete prospect: {delete_response.text}"
        
        # Verify deletion
        get_response = requests.get(f"{BASE_URL}/api/prospects", headers=self.headers)
        prospects = get_response.json()
        found = any(p["id"] == prospect_id for p in prospects)
        assert not found, "Deleted prospect should not be in list"
        
        print(f"Deleted prospect: {prospect_id}")
    
    def test_delete_nonexistent_prospect(self):
        """DELETE /api/prospects/{id} - Should return 404 for non-existent prospect"""
        fake_id = "000000000000000000000000"
        response = requests.delete(f"{BASE_URL}/api/prospects/{fake_id}", headers=self.headers)
        assert response.status_code == 404, "Should return 404 for non-existent prospect"


class TestProspectsAnalytics:
    """Test Prospects Analytics endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@immo.com",
            "password": "admin123"
        })
        assert login_response.status_code == 200
        self.token = login_response.json().get("access_token")
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def test_get_analytics(self):
        """GET /api/prospects/analytics - Get analytics data"""
        response = requests.get(f"{BASE_URL}/api/prospects/analytics", headers=self.headers)
        assert response.status_code == 200, f"Failed to get analytics: {response.text}"
        
        data = response.json()
        
        # Verify structure
        assert "total" in data, "Analytics should have total"
        assert "top_villes" in data, "Analytics should have top_villes"
        assert "top_quartiers" in data, "Analytics should have top_quartiers"
        assert "top_types" in data, "Analytics should have top_types"
        assert "objectifs" in data, "Analytics should have objectifs"
        assert "budget_avg" in data, "Analytics should have budget_avg"
        assert "modes_paiement" in data, "Analytics should have modes_paiement"
        assert "top_zones" in data, "Analytics should have top_zones"
        
        # Verify budget_avg structure
        assert "avg_min" in data["budget_avg"], "budget_avg should have avg_min"
        assert "avg_max" in data["budget_avg"], "budget_avg should have avg_max"
        
        print(f"Analytics: Total={data['total']}, Top villes={len(data['top_villes'])}, Top types={len(data['top_types'])}")
        
        # Verify top_villes structure if data exists
        if len(data["top_villes"]) > 0:
            ville = data["top_villes"][0]
            assert "name" in ville, "Ville should have name"
            assert "count" in ville, "Ville should have count"
            print(f"Top ville: {ville['name']} ({ville['count']} prospects)")


class TestProspectsExport:
    """Test Prospects Export endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@immo.com",
            "password": "admin123"
        })
        assert login_response.status_code == 200
        self.token = login_response.json().get("access_token")
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def test_export_excel(self):
        """GET /api/export/prospects/excel - Export prospects to Excel"""
        response = requests.get(f"{BASE_URL}/api/export/prospects/excel", headers=self.headers)
        assert response.status_code == 200, f"Failed to export Excel: {response.text}"
        
        # Verify content type
        content_type = response.headers.get("content-type", "")
        assert "spreadsheet" in content_type or "excel" in content_type or "octet-stream" in content_type, \
            f"Should return Excel file, got: {content_type}"
        
        # Verify content disposition
        content_disp = response.headers.get("content-disposition", "")
        assert "prospects" in content_disp.lower(), "Filename should contain 'prospects'"
        assert ".xlsx" in content_disp, "Should be .xlsx file"
        
        print(f"Excel export successful: {content_disp}")
    
    def test_export_pdf(self):
        """GET /api/export/prospects/pdf - Export prospects to PDF"""
        response = requests.get(f"{BASE_URL}/api/export/prospects/pdf", headers=self.headers)
        assert response.status_code == 200, f"Failed to export PDF: {response.text}"
        
        # Verify content type
        content_type = response.headers.get("content-type", "")
        assert "pdf" in content_type, f"Should return PDF file, got: {content_type}"
        
        # Verify content disposition
        content_disp = response.headers.get("content-disposition", "")
        assert "prospects" in content_disp.lower(), "Filename should contain 'prospects'"
        assert ".pdf" in content_disp, "Should be .pdf file"
        
        print(f"PDF export successful: {content_disp}")


class TestProspectsAuth:
    """Test that Prospects endpoints require authentication"""
    
    def test_get_prospects_requires_auth(self):
        """GET /api/prospects - Should require authentication"""
        response = requests.get(f"{BASE_URL}/api/prospects")
        assert response.status_code == 401, "Should require authentication"
    
    def test_create_prospect_requires_auth(self):
        """POST /api/prospects - Should require authentication"""
        response = requests.post(f"{BASE_URL}/api/prospects", json={"nom": "Test", "telephone": "123"})
        assert response.status_code == 401, "Should require authentication"
    
    def test_analytics_requires_auth(self):
        """GET /api/prospects/analytics - Should require authentication"""
        response = requests.get(f"{BASE_URL}/api/prospects/analytics")
        assert response.status_code == 401, "Should require authentication"
    
    def test_export_excel_requires_auth(self):
        """GET /api/export/prospects/excel - Should require authentication"""
        response = requests.get(f"{BASE_URL}/api/export/prospects/excel")
        assert response.status_code == 401, "Should require authentication"
    
    def test_export_pdf_requires_auth(self):
        """GET /api/export/prospects/pdf - Should require authentication"""
        response = requests.get(f"{BASE_URL}/api/export/prospects/pdf")
        assert response.status_code == 401, "Should require authentication"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
