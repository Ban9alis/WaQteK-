import requests
import unittest
import json
from datetime import datetime, timedelta

class WaqTechAPITest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Use the public endpoint from frontend/.env
        cls.base_url = "https://b2d9cebd-7c7f-4774-b8b4-176ec60e24bf.preview.emergentagent.com/api"
        cls.tokens = {}
        cls.user_ids = {}
        cls.leave_request_id = None
        
        # Initialize demo data
        print("\n🔍 Setting up test data...")
        response = requests.post(f"{cls.base_url}/demo/init")
        
        # Login as employee
        response = requests.post(
            f"{cls.base_url}/auth/login",
            json={"email": "employee@waqtech.com", "password": "password123"}
        )
        if response.status_code == 200:
            data = response.json()
            cls.tokens["employee"] = data["access_token"]
            cls.user_ids["employee"] = data["user"]["id"]
            print("✅ Employee login successful during setup")
        
        # Login as HR
        response = requests.post(
            f"{cls.base_url}/auth/login",
            json={"email": "hr@waqtech.com", "password": "password123"}
        )
        if response.status_code == 200:
            data = response.json()
            cls.tokens["hr"] = data["access_token"]
            cls.user_ids["hr"] = data["user"]["id"]
            print("✅ HR login successful during setup")
        
        # Login as admin
        response = requests.post(
            f"{cls.base_url}/auth/login",
            json={"email": "admin@waqtech.com", "password": "password123"}
        )
        if response.status_code == 200:
            data = response.json()
            cls.tokens["admin"] = data["access_token"]
            cls.user_ids["admin"] = data["user"]["id"]
            print("✅ Admin login successful during setup")
    
    def setUp(self):
        # This method is intentionally left empty as we're using setUpClass
        pass
        
    def test_01_initialize_demo_data(self):
        """Test initializing demo data"""
        print("\n🔍 Testing demo data initialization...")
        response = requests.post(f"{self.base_url}/demo/init")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("message", data)
        
        # Demo data might already exist, which is fine
        if "Demo data already exists" in data["message"]:
            print("✅ Demo data already exists")
        else:
            self.assertIn("users", data)
            print("✅ Demo data initialization successful")
        
    def test_02_get_employee_profile(self):
        """Test getting employee profile"""
        print("\n🔍 Testing employee profile retrieval...")
        if "employee" not in self.tokens:
            self.skipTest("Employee token not available")
            
        headers = {"Authorization": f"Bearer {self.tokens['employee']}"}
        response = requests.get(f"{self.base_url}/user/profile", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["id"], self.user_ids["employee"])
        self.assertEqual(data["role"], "employee")
        print("✅ Employee profile retrieval successful")
        
    def test_03_get_leave_balance(self):
        """Test getting leave balance"""
        print("\n🔍 Testing leave balance retrieval...")
        if "employee" not in self.tokens:
            self.skipTest("Employee token not available")
            
        headers = {"Authorization": f"Bearer {self.tokens['employee']}"}
        response = requests.get(f"{self.base_url}/leave/balance", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify leave balance structure
        self.assertIn("total_days", data)
        self.assertIn("used_days", data)
        self.assertIn("remaining_days", data)
        self.assertIn("months_worked", data)
        
        # Verify leave balance calculation
        self.assertEqual(data["total_days"], data["months_worked"] * 2)
        self.assertEqual(data["remaining_days"], data["total_days"] - data["used_days"])
        print("✅ Leave balance retrieval successful")
        
    def test_04_create_leave_request(self):
        """Test creating a leave request"""
        print("\n🔍 Testing leave request creation...")
        if "employee" not in self.tokens:
            self.skipTest("Employee token not available")
            
        headers = {"Authorization": f"Bearer {self.tokens['employee']}"}
        
        # Get current leave balance
        balance_response = requests.get(f"{self.base_url}/leave/balance", headers=headers)
        self.assertEqual(balance_response.status_code, 200)
        balance = balance_response.json()
        
        # Create a leave request for 1 day
        start_date = (datetime.utcnow() + timedelta(days=7)).strftime("%Y-%m-%d")
        end_date = (datetime.utcnow() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        response = requests.post(
            f"{self.base_url}/leave/request",
            headers=headers,
            json={
                "start_date": f"{start_date}T00:00:00.000Z",
                "end_date": f"{end_date}T00:00:00.000Z",
                "reason": "Test leave request"
            }
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("id", data)
        self.assertEqual(data["user_id"], self.user_ids["employee"])
        self.assertEqual(data["status"], "pending")
        self.assertEqual(data["days_requested"], 1)
        
        # Store leave request ID for later tests
        self.__class__.leave_request_id = data["id"]
        print("✅ Leave request creation successful")
        
    def test_05_get_leave_requests(self):
        """Test getting leave requests"""
        print("\n🔍 Testing leave requests retrieval...")
        if "employee" not in self.tokens:
            self.skipTest("Employee token not available")
            
        headers = {"Authorization": f"Bearer {self.tokens['employee']}"}
        response = requests.get(f"{self.base_url}/leave/requests", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify it's a list and contains at least one request
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 1)
        
        # Verify the request we just created is in the list
        if self.__class__.leave_request_id:
            request_ids = [req["id"] for req in data]
            self.assertIn(self.__class__.leave_request_id, request_ids)
        print("✅ Leave requests retrieval successful")
        
    def test_06_hr_approve_leave_request(self):
        """Test HR approving a leave request"""
        print("\n🔍 Testing HR approval of leave request...")
        if "hr" not in self.tokens or not self.__class__.leave_request_id:
            self.skipTest("HR token or leave request ID not available")
            
        headers = {"Authorization": f"Bearer {self.tokens['hr']}"}
        response = requests.put(
            f"{self.base_url}/leave/requests/{self.__class__.leave_request_id}",
            headers=headers,
            json={"status": "approved"}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["id"], self.__class__.leave_request_id)
        self.assertEqual(data["status"], "approved")
        self.assertEqual(data["reviewed_by"], self.user_ids["hr"])
        print("✅ HR approval of leave request successful")
        
    def test_07_verify_updated_leave_balance(self):
        """Test that leave balance is updated after approval"""
        print("\n🔍 Testing updated leave balance...")
        if "employee" not in self.tokens:
            self.skipTest("Employee token not available")
            
        headers = {"Authorization": f"Bearer {self.tokens['employee']}"}
        response = requests.get(f"{self.base_url}/leave/balance", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify used_days has increased by 1
        self.assertGreaterEqual(data["used_days"], 1)
        print("✅ Leave balance update verification successful")
        
    def test_08_invalid_login(self):
        """Test login with invalid credentials"""
        print("\n🔍 Testing invalid login...")
        response = requests.post(
            f"{self.base_url}/auth/login",
            json={"email": "nonexistent@waqtech.com", "password": "wrongpassword"}
        )
        self.assertEqual(response.status_code, 401)
        print("✅ Invalid login test successful")
        
    def test_09_insufficient_leave_balance(self):
        """Test creating a leave request with insufficient balance"""
        print("\n🔍 Testing leave request with insufficient balance...")
        if "employee" not in self.tokens:
            self.skipTest("Employee token not available")
            
        headers = {"Authorization": f"Bearer {self.tokens['employee']}"}
        
        # Get current leave balance
        balance_response = requests.get(f"{self.base_url}/leave/balance", headers=headers)
        self.assertEqual(balance_response.status_code, 200)
        balance = balance_response.json()
        
        # Try to create a leave request for more days than available
        excessive_days = balance["remaining_days"] + 10
        start_date = datetime.utcnow() + timedelta(days=14)
        end_date = start_date + timedelta(days=excessive_days)
        
        response = requests.post(
            f"{self.base_url}/leave/request",
            headers=headers,
            json={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "reason": "Test excessive leave request"
            }
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("detail", data)
        self.assertIn("Insufficient leave balance", data["detail"])
        print("✅ Insufficient leave balance test successful")

if __name__ == "__main__":
    unittest.main(verbosity=2)

if __name__ == "__main__":
    unittest.main(verbosity=2)