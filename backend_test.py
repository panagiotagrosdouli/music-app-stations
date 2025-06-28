import requests
import unittest
import json
from datetime import datetime

class GlobalMusicHubAPITester:
    def __init__(self, base_url="https://b87fb26f-ef05-40e3-bf18-641a5cc41ef2.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.test_comment_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None):
        """Run a single API test"""
        url = f"{self.base_url}{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return success, response.json()
                except:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    print(f"Response: {response.text}")
                    return False, response.json()
                except:
                    return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_health_check(self):
        """Test health check endpoint"""
        return self.run_test(
            "Health Check",
            "GET",
            "/api/health",
            200
        )

    def test_get_popular_stations(self):
        """Test getting popular stations"""
        return self.run_test(
            "Get Popular Stations",
            "GET",
            "/api/stations/popular?limit=10",
            200
        )

    def test_get_countries(self):
        """Test getting countries list"""
        return self.run_test(
            "Get Countries",
            "GET",
            "/api/countries",
            200
        )

    def test_get_stations_by_country(self, country="Germany"):
        """Test getting stations by country"""
        return self.run_test(
            f"Get Stations by Country ({country})",
            "GET",
            f"/api/stations/by-country/{country}?limit=10",
            200
        )

    def test_search_stations(self, query="rock"):
        """Test searching stations"""
        return self.run_test(
            f"Search Stations ({query})",
            "GET",
            f"/api/stations/search?q={query}&limit=10",
            200
        )

    def test_create_comment(self, station_id):
        """Test creating a comment"""
        data = {
            "content": "This is a test comment from API testing",
            "author": "API Tester",
            "target_id": station_id,
            "target_type": "station"
        }
        success, response = self.run_test(
            "Create Comment",
            "POST",
            "/api/comments",
            200,
            data=data
        )
        if success and 'id' in response:
            self.test_comment_id = response['id']
        return success, response

    def test_get_comments(self, station_id):
        """Test getting comments for a station"""
        return self.run_test(
            "Get Comments",
            "GET",
            f"/api/comments/{station_id}?target_type=station",
            200
        )

    def test_delete_comment(self):
        """Test deleting a comment"""
        if not self.test_comment_id:
            print("❌ No comment ID available for deletion test")
            return False, {}
        
        return self.run_test(
            "Delete Comment",
            "DELETE",
            f"/api/comments/{self.test_comment_id}",
            200
        )

def main():
    # Setup
    tester = GlobalMusicHubAPITester()
    station_id = None

    # Run tests
    print("\n===== Testing Global Music Hub API =====\n")
    
    # Test health check
    tester.test_health_check()
    
    # Test getting popular stations
    success, stations = tester.test_get_popular_stations()
    if success and stations and len(stations) > 0:
        station_id = stations[0]['stationuuid']
        print(f"Using station ID: {station_id} for comment tests")
    
    # Test getting countries
    tester.test_get_countries()
    
    # Test getting stations by country
    tester.test_get_stations_by_country()
    
    # Test searching stations
    tester.test_search_stations()
    
    # Test comments functionality if we have a station ID
    if station_id:
        # Create a comment
        tester.test_create_comment(station_id)
        
        # Get comments for the station
        tester.test_get_comments(station_id)
        
        # Delete the comment we created
        if tester.test_comment_id:
            tester.test_delete_comment()
    
    # Print results
    print(f"\n===== Test Results =====")
    print(f"Tests passed: {tester.tests_passed}/{tester.tests_run}")
    print(f"Success rate: {(tester.tests_passed/tester.tests_run)*100:.2f}%")
    
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    main()