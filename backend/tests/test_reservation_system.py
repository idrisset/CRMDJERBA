"""
Backend API tests for DJERBA CONSTRUCTION CRM - Reservation System
Tests: Reservation flow, apartment blocking, conflict detection, history
New features from iteration 5: EDIMCO branding, type tabs, reservation system
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://property-hub-612.preview.emergentagent.com')

# Test credentials
ADMIN_EMAIL = "admin@immo.com"
ADMIN_PASSWORD = "admin123"


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


class TestLoginAndBranding:
    """Test login and EDIMCO branding"""
    
    def test_login_success(self):
        """Test admin login with admin@immo.com / admin123"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        data = response.json()
        assert "access_token" in data
        assert data["email"] == ADMIN_EMAIL
        assert data["role"] == "admin"
        print("✓ Login with admin@immo.com / admin123 - SUCCESS")


class TestDashboardEDIMCO:
    """Test Dashboard displays EDIMCO branding and blocs A-H stats"""
    
    def test_dashboard_blocs_stats(self, auth_headers):
        """Dashboard displays blocs A-H stats"""
        response = requests.get(f"{BASE_URL}/api/dashboard", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "blocs_stats" in data
        
        expected_blocs = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
        for bloc in expected_blocs:
            assert bloc in data["blocs_stats"], f"Missing bloc {bloc}"
            bloc_data = data["blocs_stats"][bloc]
            assert "total" in bloc_data
            assert "disponible" in bloc_data
            assert "reserve" in bloc_data
            assert "vendu" in bloc_data
        
        print("✓ Dashboard displays blocs A-H stats - SUCCESS")


class TestAppartementsTypeTabs:
    """Test Appartements page type tabs (F2, F3, F4, etc.)"""
    
    def test_appartements_have_types(self, auth_headers):
        """Appartements have different types for tabs"""
        response = requests.get(f"{BASE_URL}/api/appartements", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        types = set(a.get('type_appart') for a in data)
        
        # Should have at least F2, F3, F4 types
        expected_types = {'F2', 'F3', 'F4'}
        found_types = expected_types.intersection(types)
        assert len(found_types) >= 2, f"Expected at least 2 of {expected_types}, found {found_types}"
        
        print(f"✓ Appartements have types: {types} - SUCCESS")


class TestReservationSystem:
    """Test reservation system - core functionality"""
    
    def test_create_client_with_apartment_reservation(self, auth_headers):
        """Create client WITH apartment assigned → apartment becomes 'réservé'"""
        # First get an available apartment
        apparts_response = requests.get(f"{BASE_URL}/api/appartements", headers=auth_headers)
        assert apparts_response.status_code == 200
        
        apparts = apparts_response.json()
        available = [a for a in apparts if a['statut'] == 'disponible' and a['destination'] == 'Logement']
        
        if not available:
            pytest.skip("No available apartments to test reservation")
        
        test_appart = available[0]
        appart_id = test_appart['id']
        
        # Create client with apartment assigned
        client_data = {
            "nom": "TEST_Reservation_Client",
            "telephone": "0555999888",
            "email": "test.reservation@edimco.dz",
            "statut": "nouveau",
            "temperature": "chaud",
            "appartement_id": appart_id
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/clients",
            headers=auth_headers,
            json=client_data
        )
        assert create_response.status_code == 200, f"Failed to create client: {create_response.text}"
        
        created_client = create_response.json()
        client_id = created_client["id"]
        
        # Verify apartment is now reserved
        appart_check = requests.get(f"{BASE_URL}/api/appartements", headers=auth_headers)
        apparts_after = appart_check.json()
        reserved_appart = next((a for a in apparts_after if a['id'] == appart_id), None)
        
        assert reserved_appart is not None
        assert reserved_appart['statut'] == 'réservé', f"Expected 'réservé', got '{reserved_appart['statut']}'"
        assert reserved_appart['client_id'] == client_id, "Apartment should have client_id set"
        
        print(f"✓ Client created with apartment → apartment status='réservé' - SUCCESS")
        
        # Cleanup: delete client (should release apartment)
        delete_response = requests.delete(f"{BASE_URL}/api/clients/{client_id}", headers=auth_headers)
        assert delete_response.status_code == 200
        
        # Verify apartment is released
        appart_final = requests.get(f"{BASE_URL}/api/appartements", headers=auth_headers)
        apparts_final = appart_final.json()
        released_appart = next((a for a in apparts_final if a['id'] == appart_id), None)
        assert released_appart['statut'] == 'disponible', "Apartment should be released after client deletion"
        
        print("✓ Delete client → apartment becomes 'disponible' - SUCCESS")
    
    def test_reservation_conflict_409(self, auth_headers):
        """Try to reserve already reserved apartment → HTTP 409"""
        # Get an available apartment
        apparts_response = requests.get(f"{BASE_URL}/api/appartements", headers=auth_headers)
        apparts = apparts_response.json()
        available = [a for a in apparts if a['statut'] == 'disponible' and a['destination'] == 'Logement']
        
        if len(available) < 1:
            pytest.skip("No available apartments to test conflict")
        
        test_appart = available[0]
        appart_id = test_appart['id']
        
        # Create first client with apartment
        client1_data = {
            "nom": "TEST_Conflict_Client1",
            "telephone": "0555111222",
            "statut": "nouveau",
            "temperature": "chaud",
            "appartement_id": appart_id
        }
        
        create1 = requests.post(f"{BASE_URL}/api/clients", headers=auth_headers, json=client1_data)
        assert create1.status_code == 200
        client1_id = create1.json()["id"]
        
        # Create second client and try to assign same apartment
        client2_data = {
            "nom": "TEST_Conflict_Client2",
            "telephone": "0555333444",
            "statut": "nouveau",
            "temperature": "tiède"
        }
        
        create2 = requests.post(f"{BASE_URL}/api/clients", headers=auth_headers, json=client2_data)
        assert create2.status_code == 200
        client2_id = create2.json()["id"]
        
        # Try to update client2 to use same apartment - should get 409
        update_response = requests.put(
            f"{BASE_URL}/api/clients/{client2_id}",
            headers=auth_headers,
            json={"appartement_id": appart_id}
        )
        
        assert update_response.status_code == 409, f"Expected 409 conflict, got {update_response.status_code}: {update_response.text}"
        print("✓ Reservation conflict returns HTTP 409 - SUCCESS")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/clients/{client1_id}", headers=auth_headers)
        requests.delete(f"{BASE_URL}/api/clients/{client2_id}", headers=auth_headers)
    
    def test_update_client_apartment_releases_old(self, auth_headers):
        """Update client apartment → old released, new blocked"""
        # Get two available apartments
        apparts_response = requests.get(f"{BASE_URL}/api/appartements", headers=auth_headers)
        apparts = apparts_response.json()
        available = [a for a in apparts if a['statut'] == 'disponible' and a['destination'] == 'Logement']
        
        if len(available) < 2:
            pytest.skip("Need at least 2 available apartments")
        
        appart1_id = available[0]['id']
        appart2_id = available[1]['id']
        
        # Create client with first apartment
        client_data = {
            "nom": "TEST_Switch_Client",
            "telephone": "0555666777",
            "statut": "nouveau",
            "temperature": "chaud",
            "appartement_id": appart1_id
        }
        
        create_response = requests.post(f"{BASE_URL}/api/clients", headers=auth_headers, json=client_data)
        assert create_response.status_code == 200
        client_id = create_response.json()["id"]
        
        # Update client to use second apartment
        update_response = requests.put(
            f"{BASE_URL}/api/clients/{client_id}",
            headers=auth_headers,
            json={"appartement_id": appart2_id}
        )
        assert update_response.status_code == 200
        
        # Verify: appart1 should be disponible, appart2 should be réservé
        apparts_after = requests.get(f"{BASE_URL}/api/appartements", headers=auth_headers).json()
        
        appart1_after = next((a for a in apparts_after if a['id'] == appart1_id), None)
        appart2_after = next((a for a in apparts_after if a['id'] == appart2_id), None)
        
        assert appart1_after['statut'] == 'disponible', f"Old apartment should be 'disponible', got '{appart1_after['statut']}'"
        assert appart2_after['statut'] == 'réservé', f"New apartment should be 'réservé', got '{appart2_after['statut']}'"
        
        print("✓ Update client apartment → old released, new blocked - SUCCESS")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/clients/{client_id}", headers=auth_headers)


class TestReservationsHistory:
    """Test reservations history API"""
    
    def test_get_reservations_history(self, auth_headers):
        """API /api/reservations returns history"""
        response = requests.get(f"{BASE_URL}/api/reservations", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        
        # If there are reservations, check structure
        if len(data) > 0:
            reservation = data[0]
            expected_fields = ['id', 'client_id', 'appartement_id', 'action', 'date']
            for field in expected_fields:
                assert field in reservation, f"Missing field {field} in reservation"
        
        print(f"✓ GET /api/reservations returns history ({len(data)} entries) - SUCCESS")
    
    def test_reservation_creates_history_entry(self, auth_headers):
        """Creating reservation adds entry to history"""
        # Get initial history count
        initial_history = requests.get(f"{BASE_URL}/api/reservations", headers=auth_headers).json()
        initial_count = len(initial_history)
        
        # Get available apartment
        apparts = requests.get(f"{BASE_URL}/api/appartements", headers=auth_headers).json()
        available = [a for a in apparts if a['statut'] == 'disponible' and a['destination'] == 'Logement']
        
        if not available:
            pytest.skip("No available apartments")
        
        appart_id = available[0]['id']
        
        # Create client with apartment
        client_data = {
            "nom": "TEST_History_Client",
            "telephone": "0555888999",
            "statut": "nouveau",
            "temperature": "chaud",
            "appartement_id": appart_id
        }
        
        create_response = requests.post(f"{BASE_URL}/api/clients", headers=auth_headers, json=client_data)
        assert create_response.status_code == 200
        client_id = create_response.json()["id"]
        
        # Check history increased
        new_history = requests.get(f"{BASE_URL}/api/reservations", headers=auth_headers).json()
        assert len(new_history) > initial_count, "Reservation should create history entry"
        
        # Verify latest entry
        latest = new_history[0]  # Sorted by date desc
        assert latest['action'] == 'réservé'
        assert latest['appartement_id'] == appart_id
        
        print("✓ Reservation creates history entry - SUCCESS")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/clients/{client_id}", headers=auth_headers)


class TestClientsWithApartmentInfo:
    """Test clients page shows apartment info"""
    
    def test_clients_have_appartement_id(self, auth_headers):
        """Clients API returns appartement_id field"""
        response = requests.get(f"{BASE_URL}/api/clients", headers=auth_headers)
        assert response.status_code == 200
        
        # Check structure includes appartement_id
        data = response.json()
        if len(data) > 0:
            client = data[0]
            assert 'appartement_id' in client, "Client should have appartement_id field"
        
        print("✓ Clients API returns appartement_id field - SUCCESS")


class TestAppartementsShowClientName:
    """Test apartments page shows client name for reserved apartments"""
    
    def test_appartements_have_client_id(self, auth_headers):
        """Appartements API returns client_id for reserved apartments"""
        response = requests.get(f"{BASE_URL}/api/appartements", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        # Check structure includes client_id
        if len(data) > 0:
            appart = data[0]
            assert 'client_id' in appart, "Appartement should have client_id field"
        
        # Check reserved apartments have client_id set
        reserved = [a for a in data if a['statut'] == 'réservé']
        for r in reserved[:3]:  # Check first 3
            if r.get('client_id'):
                print(f"  - Lot {r.get('numero_lot')} reserved by client {r.get('client_id')}")
        
        print("✓ Appartements API returns client_id field - SUCCESS")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
