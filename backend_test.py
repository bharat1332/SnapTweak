import requests
import unittest
import uuid
import time
from datetime import datetime

class MusicAppAPITester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.token = None
        self.username = f"test_user_{int(time.time())}"
        self.email = f"{self.username}@test.com"
        self.password = "Test123!"
        self.test_results = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "details": []
        }

    def run_test(self, name, test_func):
        """Run a test and record results"""
        self.test_results["total"] += 1
        print(f"\n🔍 Testing: {name}")
        
        try:
            result = test_func()
            if result:
                self.test_results["passed"] += 1
                status = "✅ PASSED"
            else:
                self.test_results["failed"] += 1
                status = "❌ FAILED"
        except Exception as e:
            self.test_results["failed"] += 1
            status = f"❌ ERROR: {str(e)}"
        
        self.test_results["details"].append({
            "name": name,
            "status": status
        })
        
        print(f"Result: {status}")
        return result

    def register_user(self):
        """Test user registration"""
        url = f"{self.base_url}/api/auth/register"
        data = {
            "username": self.username,
            "email": self.email,
            "password": self.password
        }
        
        response = requests.post(url, json=data)
        
        if response.status_code == 200:
            result = response.json()
            self.token = result.get("access_token")
            print(f"  User registered: {self.username}")
            print(f"  Token received: {self.token[:10]}...")
            return True
        else:
            print(f"  Registration failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return False

    def login_user(self):
        """Test user login"""
        url = f"{self.base_url}/api/auth/login"
        data = {
            "username": self.username,
            "password": self.password
        }
        
        response = requests.post(url, json=data)
        
        if response.status_code == 200:
            result = response.json()
            self.token = result.get("access_token")
            print(f"  Login successful: {self.username}")
            print(f"  Token received: {self.token[:10]}...")
            return True
        else:
            print(f"  Login failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return False

    def get_user_info(self):
        """Test getting user info"""
        if not self.token:
            print("  No token available")
            return False
            
        url = f"{self.base_url}/api/auth/me"
        headers = {"Authorization": f"Bearer {self.token}"}
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            user_info = response.json()
            print(f"  User info: {user_info}")
            return user_info.get("username") == self.username
        else:
            print(f"  Get user info failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return False

    def get_tracks(self):
        """Test getting all tracks"""
        url = f"{self.base_url}/api/tracks"
        
        response = requests.get(url)
        
        if response.status_code == 200:
            tracks = response.json()
            print(f"  Retrieved {len(tracks)} tracks")
            return len(tracks) > 0
        else:
            print(f"  Get tracks failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return False

    def search_tracks(self, query="jazz"):
        """Test track search functionality"""
        url = f"{self.base_url}/api/tracks/search/{query}"
        
        response = requests.get(url)
        
        if response.status_code == 200:
            results = response.json()
            print(f"  Search for '{query}' returned {len(results)} results")
            return True
        else:
            print(f"  Search failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return False

    def create_playlist(self, name=None):
        """Test creating a playlist"""
        if not self.token:
            print("  No token available")
            return None
            
        url = f"{self.base_url}/api/playlists"
        headers = {"Authorization": f"Bearer {self.token}"}
        
        if name is None:
            name = f"Test Playlist {int(time.time())}"
            
        data = {
            "name": name,
            "description": "Created by automated test",
            "track_ids": []
        }
        
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            playlist_id = result.get("playlist_id")
            print(f"  Playlist created: {name} (ID: {playlist_id})")
            return playlist_id
        else:
            print(f"  Create playlist failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return None

    def get_playlists(self):
        """Test getting user playlists"""
        if not self.token:
            print("  No token available")
            return False
            
        url = f"{self.base_url}/api/playlists"
        headers = {"Authorization": f"Bearer {self.token}"}
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            playlists = response.json()
            print(f"  Retrieved {len(playlists)} playlists")
            return True
        else:
            print(f"  Get playlists failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return False

    def add_track_to_playlist(self, playlist_id, track_id="1"):
        """Test adding a track to a playlist"""
        if not self.token:
            print("  No token available")
            return False
            
        url = f"{self.base_url}/api/playlists/{playlist_id}"
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # First get the current playlist to get existing track_ids
        get_response = requests.get(url, headers=headers)
        if get_response.status_code != 200:
            print(f"  Failed to get playlist: {get_response.status_code}")
            return False
            
        playlist = get_response.json()
        track_ids = playlist.get("track_ids", [])
        
        # Add the new track_id if not already present
        if track_id not in track_ids:
            track_ids.append(track_id)
        
        data = {
            "track_ids": track_ids
        }
        
        response = requests.put(url, json=data, headers=headers)
        
        if response.status_code == 200:
            print(f"  Added track {track_id} to playlist {playlist_id}")
            return True
        else:
            print(f"  Add track to playlist failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return False

    def get_playlist(self, playlist_id):
        """Test getting a specific playlist"""
        if not self.token:
            print("  No token available")
            return False
            
        url = f"{self.base_url}/api/playlists/{playlist_id}"
        headers = {"Authorization": f"Bearer {self.token}"}
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            playlist = response.json()
            print(f"  Retrieved playlist: {playlist['name']}")
            print(f"  Tracks in playlist: {len(playlist.get('tracks', []))}")
            return True
        else:
            print(f"  Get playlist failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return False

    def delete_playlist(self, playlist_id):
        """Test deleting a playlist"""
        if not self.token:
            print("  No token available")
            return False
            
        url = f"{self.base_url}/api/playlists/{playlist_id}"
        headers = {"Authorization": f"Bearer {self.token}"}
        
        response = requests.delete(url, headers=headers)
        
        if response.status_code == 200:
            print(f"  Deleted playlist: {playlist_id}")
            return True
        else:
            print(f"  Delete playlist failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return False

    def run_all_tests(self):
        """Run all API tests in sequence"""
        print("🎵 Starting Music App API Tests 🎵")
        print(f"Base URL: {self.base_url}")
        print(f"Test user: {self.username}")
        
        # Authentication tests
        self.run_test("User Registration", self.register_user)
        self.run_test("User Login", self.login_user)
        self.run_test("Get User Info", self.get_user_info)
        
        # Track tests
        self.run_test("Get All Tracks", self.get_tracks)
        self.run_test("Search Tracks", self.search_tracks)
        
        # Playlist tests
        playlist_id = None
        if self.run_test("Create Playlist", lambda: self.create_playlist() is not None):
            playlist_id = self.create_playlist()
            
        self.run_test("Get User Playlists", self.get_playlists)
        
        if playlist_id:
            self.run_test("Add Track to Playlist", lambda: self.add_track_to_playlist(playlist_id))
            self.run_test("Get Specific Playlist", lambda: self.get_playlist(playlist_id))
            self.run_test("Delete Playlist", lambda: self.delete_playlist(playlist_id))
        
        # Print summary
        print("\n📊 Test Results Summary:")
        print(f"Total tests: {self.test_results['total']}")
        print(f"Passed: {self.test_results['passed']}")
        print(f"Failed: {self.test_results['failed']}")
        
        for test in self.test_results["details"]:
            print(f"  {test['name']}: {test['status']}")
            
        return self.test_results["failed"] == 0

if __name__ == "__main__":
    # Get the backend URL from the frontend .env file
    import os
    
    # Use the public endpoint from frontend/.env
    with open('/app/frontend/.env', 'r') as f:
        for line in f:
            if line.startswith('REACT_APP_BACKEND_URL='):
                backend_url = line.strip().split('=')[1]
                break
    
    tester = MusicAppAPITester(backend_url)
    success = tester.run_all_tests()
    
    exit(0 if success else 1)