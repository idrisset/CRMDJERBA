import requests
import sys
import json
from datetime import datetime

class CRMAPITester:
    def __init__(self, base_url="https://property-hub-612.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
        self.tests_run = 0
        self.tests_passed = 0
        self.admin_user = None

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        return success

    def test_auth_login(self):
        """Test admin login"""
        print("\n🔍 Testing Authentication...")
        
        try:
            response = self.session.post(
                f"{self.base_url}/auth/login",
                json={"email": "admin@immo.com", "password": "admin123"}
            )
            
            if response.status_code == 200:
                self.admin_user = response.json()
                # Check if cookies are set
                cookies_set = 'access_token' in response.cookies
                return self.log_test("Admin Login", True, f"User: {self.admin_user.get('name', 'N/A')}, Cookies: {cookies_set}")
            else:
                return self.log_test("Admin Login", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            return self.log_test("Admin Login", False, f"Exception: {str(e)}")

    def test_auth_me(self):
        """Test getting current user info"""
        try:
            response = self.session.get(f"{self.base_url}/auth/me")
            
            if response.status_code == 200:
                user_data = response.json()
                is_admin = user_data.get('role') == 'admin'
                return self.log_test("Get Current User", True, f"Role: {user_data.get('role')}, Admin: {is_admin}")
            else:
                return self.log_test("Get Current User", False, f"Status: {response.status_code}")
                
        except Exception as e:
            return self.log_test("Get Current User", False, f"Exception: {str(e)}")

    def test_dashboard_stats(self):
        """Test dashboard statistics"""
        print("\n🔍 Testing Dashboard...")
        
        try:
            response = self.session.get(f"{self.base_url}/dashboard")
            
            if response.status_code == 200:
                stats = response.json()
                required_fields = ['total_clients', 'total_appartements', 'appartements_disponibles', 
                                 'appartements_reserves', 'appartements_vendus', 'clients_par_statut']
                
                missing_fields = [field for field in required_fields if field not in stats]
                if not missing_fields:
                    return self.log_test("Dashboard Stats", True, f"Total clients: {stats.get('total_clients', 0)}")
                else:
                    return self.log_test("Dashboard Stats", False, f"Missing fields: {missing_fields}")
            else:
                return self.log_test("Dashboard Stats", False, f"Status: {response.status_code}")
                
        except Exception as e:
            return self.log_test("Dashboard Stats", False, f"Exception: {str(e)}")

    def test_residences_crud(self):
        """Test residences CRUD operations"""
        print("\n🔍 Testing Residences...")
        
        # Get residences
        try:
            response = self.session.get(f"{self.base_url}/residences")
            if response.status_code == 200:
                residences = response.json()
                self.log_test("Get Residences", True, f"Found {len(residences)} residences")
                return True
            else:
                return self.log_test("Get Residences", False, f"Status: {response.status_code}")
        except Exception as e:
            return self.log_test("Get Residences", False, f"Exception: {str(e)}")

    def test_clients_crud(self):
        """Test clients CRUD operations"""
        print("\n🔍 Testing Clients...")
        
        # Get clients
        try:
            response = self.session.get(f"{self.base_url}/clients")
            if response.status_code == 200:
                clients = response.json()
                self.log_test("Get Clients", True, f"Found {len(clients)} clients")
                
                # Test creating a client
                test_client = {
                    "nom": "Test Client",
                    "telephone": "+33123456789",
                    "email": "test@example.com",
                    "statut": "nouveau"
                }
                
                create_response = self.session.post(f"{self.base_url}/clients", json=test_client)
                if create_response.status_code == 200:
                    created_client = create_response.json()
                    client_id = created_client.get('id')
                    self.log_test("Create Client", True, f"Created client ID: {client_id}")
                    
                    # Test updating the client
                    update_data = {"statut": "intéressé", "notes": "Test update"}
                    update_response = self.session.put(f"{self.base_url}/clients/{client_id}", json=update_data)
                    if update_response.status_code == 200:
                        self.log_test("Update Client", True, "Client updated successfully")
                    else:
                        self.log_test("Update Client", False, f"Status: {update_response.status_code}")
                    
                    # Test deleting the client
                    delete_response = self.session.delete(f"{self.base_url}/clients/{client_id}")
                    if delete_response.status_code == 200:
                        self.log_test("Delete Client", True, "Client deleted successfully")
                    else:
                        self.log_test("Delete Client", False, f"Status: {delete_response.status_code}")
                        
                else:
                    self.log_test("Create Client", False, f"Status: {create_response.status_code}")
                    
                return True
            else:
                return self.log_test("Get Clients", False, f"Status: {response.status_code}")
        except Exception as e:
            return self.log_test("Get Clients", False, f"Exception: {str(e)}")

    def test_appartements_crud(self):
        """Test appartements CRUD operations"""
        print("\n🔍 Testing Appartements...")
        
        # Get appartements
        try:
            response = self.session.get(f"{self.base_url}/appartements")
            if response.status_code == 200:
                appartements = response.json()
                self.log_test("Get Appartements", True, f"Found {len(appartements)} appartements")
                return True
            else:
                return self.log_test("Get Appartements", False, f"Status: {response.status_code}")
        except Exception as e:
            return self.log_test("Get Appartements", False, f"Exception: {str(e)}")

    def test_whatsapp_ai(self):
        """Test WhatsApp AI functionality"""
        print("\n🔍 Testing WhatsApp AI...")
        
        try:
            # Test sending a message to AI
            test_message = {
                "phone": "+33612345678",
                "message": "Bonjour, je cherche un appartement F2"
            }
            
            response = self.session.post(f"{self.base_url}/whatsapp/message", json=test_message)
            
            if response.status_code == 200:
                ai_response = response.json()
                if 'response' in ai_response:
                    self.log_test("WhatsApp AI Message", True, f"AI responded: {ai_response['response'][:50]}...")
                else:
                    self.log_test("WhatsApp AI Message", False, "No response field in AI response")
            else:
                self.log_test("WhatsApp AI Message", False, f"Status: {response.status_code}, Response: {response.text}")
            
            # Test getting conversations
            conv_response = self.session.get(f"{self.base_url}/whatsapp/conversations")
            if conv_response.status_code == 200:
                conversations = conv_response.json()
                self.log_test("Get WhatsApp Conversations", True, f"Found {len(conversations)} conversations")
            else:
                self.log_test("Get WhatsApp Conversations", False, f"Status: {conv_response.status_code}")
                
        except Exception as e:
            self.log_test("WhatsApp AI", False, f"Exception: {str(e)}")

    def test_admin_only_endpoints(self):
        """Test admin-only endpoints"""
        print("\n🔍 Testing Admin-Only Endpoints...")
        
        try:
            # Test getting users (admin only)
            response = self.session.get(f"{self.base_url}/users")
            if response.status_code == 200:
                users = response.json()
                self.log_test("Get Users (Admin)", True, f"Found {len(users)} users")
            else:
                self.log_test("Get Users (Admin)", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Get Users (Admin)", False, f"Exception: {str(e)}")

    def test_logout(self):
        """Test logout"""
        print("\n🔍 Testing Logout...")
        
        try:
            response = self.session.post(f"{self.base_url}/auth/logout")
            if response.status_code == 200:
                return self.log_test("Logout", True, "Successfully logged out")
            else:
                return self.log_test("Logout", False, f"Status: {response.status_code}")
        except Exception as e:
            return self.log_test("Logout", False, f"Exception: {str(e)}")

    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting CRM API Tests...")
        print(f"Testing against: {self.base_url}")
        
        # Authentication tests
        if not self.test_auth_login():
            print("❌ Login failed - stopping tests")
            return False
            
        self.test_auth_me()
        
        # Core functionality tests
        self.test_dashboard_stats()
        self.test_residences_crud()
        self.test_clients_crud()
        self.test_appartements_crud()
        self.test_whatsapp_ai()
        self.test_admin_only_endpoints()
        
        # Cleanup
        self.test_logout()
        
        # Print summary
        print(f"\n📊 Test Summary:")
        print(f"Tests run: {self.tests_run}")
        print(f"Tests passed: {self.tests_passed}")
        print(f"Success rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        return self.tests_passed == self.tests_run

def main():
    tester = CRMAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())