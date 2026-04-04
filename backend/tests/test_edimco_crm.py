"""
Backend API tests for DJERBA CONSTRUCTION CRM - EDIMCO Project
Tests: Auth, Dashboard, Appartements (298 lots), Clients, Residences
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://property-hub-612.preview.emergentagent.com')

# Test credentials
ADMIN_EMAIL = "admin@immo.com"
ADMIN_PASSWORD = "admin123"


class TestAuth:
    """Authentication endpoint tests"""
    
    def test_login_success(self):
        """Test admin login with correct credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        data = response.json()
        assert "access_token" in data, "Missing access_token"
        assert "refresh_token" in data, "Missing refresh_token"
        assert data["email"] == ADMIN_EMAIL
        assert data["role"] == "admin"
        assert data["name"] == "Administrateur"
    
    def test_login_invalid_credentials(self):
        """Test login with wrong password"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": "wrongpassword"
        })
        assert response.status_code == 401
    
    def test_auth_me_without_token(self):
        """Test /auth/me without token returns 401"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 401


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for tests"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Authentication failed")


@pytest.fixture
def auth_headers(auth_token):
    """Headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestDashboard:
    """Dashboard API tests - EDIMCO stats"""
    
    def test_dashboard_returns_edimco_stats(self, auth_headers):
        """Test dashboard returns correct EDIMCO statistics"""
        response = requests.get(f"{BASE_URL}/api/dashboard", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify total logements (264 as per EDIMCO spec)
        assert "total_logements" in data
        assert data["total_logements"] == 264, f"Expected 264 logements, got {data['total_logements']}"
        
        # Verify blocs_stats has 8 blocs (A-H)
        assert "blocs_stats" in data
        blocs = data["blocs_stats"]
        expected_blocs = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
        assert set(blocs.keys()) == set(expected_blocs), f"Expected blocs {expected_blocs}, got {list(blocs.keys())}"
        
        # Verify each bloc has required stats
        for bloc in expected_blocs:
            assert "total" in blocs[bloc]
            assert "disponible" in blocs[bloc]
            assert "reserve" in blocs[bloc]
            assert "vendu" in blocs[bloc]
    
    def test_dashboard_client_stats(self, auth_headers):
        """Test dashboard returns client statistics"""
        response = requests.get(f"{BASE_URL}/api/dashboard", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "total_clients" in data
        assert "clients_par_statut" in data
        assert "clients_par_temperature" in data
        
        # Verify temperature keys
        temps = data["clients_par_temperature"]
        assert "chaud" in temps
        assert "tiède" in temps
        assert "froid" in temps


class TestAppartements:
    """Appartements API tests - 298 EDIMCO lots"""
    
    def test_get_all_appartements_returns_298(self, auth_headers):
        """Test GET /appartements returns 298 lots"""
        response = requests.get(f"{BASE_URL}/api/appartements", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 298, f"Expected 298 lots, got {len(data)}"
    
    def test_appartements_have_required_fields(self, auth_headers):
        """Test appartements have all required EDIMCO fields"""
        response = requests.get(f"{BASE_URL}/api/appartements", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        required_fields = ['id', 'residence_id', 'type_appart', 'prix', 'etage', 
                          'statut', 'surface_habitable', 'surface_utile', 
                          'bloc', 'numero_lot', 'destination']
        
        for appart in data[:5]:  # Check first 5
            for field in required_fields:
                assert field in appart, f"Missing field {field} in appartement"
    
    def test_appartements_destinations(self, auth_headers):
        """Test appartements have correct destinations breakdown"""
        response = requests.get(f"{BASE_URL}/api/appartements", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        destinations = {}
        for a in data:
            dest = a.get('destination', 'Unknown')
            destinations[dest] = destinations.get(dest, 0) + 1
        
        # Expected: 264 Logement, 8 Commerce, 24 Service, 1 Parking, 1 Creche (total 298)
        assert destinations.get('Logement', 0) == 264, f"Expected 264 Logement, got {destinations.get('Logement', 0)}"
        assert destinations.get('Commerce', 0) == 8, f"Expected 8 Commerce, got {destinations.get('Commerce', 0)}"
        assert destinations.get('Service', 0) >= 24, f"Expected at least 24 Service, got {destinations.get('Service', 0)}"
    
    def test_appartements_blocs(self, auth_headers):
        """Test appartements are distributed across blocs A-H"""
        response = requests.get(f"{BASE_URL}/api/appartements", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        blocs = set(a.get('bloc') for a in data if a.get('destination') == 'Logement')
        expected_blocs = {'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'}
        
        assert expected_blocs.issubset(blocs), f"Missing blocs. Found: {blocs}"
    
    def test_update_appartement_status(self, auth_headers):
        """Test updating appartement status"""
        # Get first available appartement
        response = requests.get(f"{BASE_URL}/api/appartements", headers=auth_headers)
        data = response.json()
        
        # Find a logement to update
        logement = next((a for a in data if a['destination'] == 'Logement' and a['statut'] == 'disponible'), None)
        if not logement:
            pytest.skip("No available logement to test")
        
        appart_id = logement['id']
        
        # Update status to réservé
        update_response = requests.put(
            f"{BASE_URL}/api/appartements/{appart_id}",
            headers=auth_headers,
            json={"statut": "réservé"}
        )
        assert update_response.status_code == 200
        
        # Verify update
        updated = update_response.json()
        assert updated["statut"] == "réservé"
        
        # Revert back to disponible
        revert_response = requests.put(
            f"{BASE_URL}/api/appartements/{appart_id}",
            headers=auth_headers,
            json={"statut": "disponible"}
        )
        assert revert_response.status_code == 200


class TestResidences:
    """Residences API tests"""
    
    def test_get_residences_includes_edimco(self, auth_headers):
        """Test EDIMCO residence exists"""
        response = requests.get(f"{BASE_URL}/api/residences", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        edimco = next((r for r in data if r['nom'] == 'EDIMCO'), None)
        assert edimco is not None, "EDIMCO residence not found"
        # Address may use accented "Béjaïa" or plain "Bejaia"
        address = edimco.get('adresse', '').lower()
        assert "beja" in address or "béja" in address, f"EDIMCO address should mention Bejaia, got: {edimco.get('adresse', '')}"


class TestClients:
    """Clients API tests"""
    
    def test_get_clients(self, auth_headers):
        """Test GET /clients"""
        response = requests.get(f"{BASE_URL}/api/clients", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_create_and_delete_client(self, auth_headers):
        """Test client CRUD operations"""
        # Create client
        client_data = {
            "nom": "TEST_Client EDIMCO",
            "telephone": "0555123456",
            "email": "test@edimco.dz",
            "statut": "nouveau",
            "temperature": "tiède"
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/clients",
            headers=auth_headers,
            json=client_data
        )
        assert create_response.status_code == 200
        
        created = create_response.json()
        assert created["nom"] == client_data["nom"]
        assert created["telephone"] == client_data["telephone"]
        assert "id" in created
        
        client_id = created["id"]
        
        # Verify client exists
        get_response = requests.get(f"{BASE_URL}/api/clients", headers=auth_headers)
        clients = get_response.json()
        found = any(c["id"] == client_id for c in clients)
        assert found, "Created client not found in list"
        
        # Delete client
        delete_response = requests.delete(
            f"{BASE_URL}/api/clients/{client_id}",
            headers=auth_headers
        )
        assert delete_response.status_code == 200


class TestExport:
    """Export API tests"""
    
    def test_export_appartements_excel(self, auth_headers):
        """Test Excel export endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/export/appartements/excel",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert "spreadsheet" in response.headers.get("content-type", "")
    
    def test_export_clients_excel(self, auth_headers):
        """Test clients Excel export"""
        response = requests.get(
            f"{BASE_URL}/api/export/clients/excel",
            headers=auth_headers
        )
        assert response.status_code == 200


class TestAPIRoot:
    """API root endpoint test"""
    
    def test_api_health(self):
        """Test API is accessible via auth endpoint"""
        # API root may not be exposed, test via login endpoint
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "test"
        })
        # Should return 401 (unauthorized) not 500 or connection error
        assert response.status_code in [401, 400], f"API not healthy: {response.status_code}"
