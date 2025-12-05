"""
Tests for the Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add the src directory to the path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to original state before each test"""
    # Store original state
    original_activities = {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        },
        "Basketball Team": {
            "description": "Competitive basketball team with games and practices",
            "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
            "max_participants": 15,
            "participants": ["alex@mergington.edu"]
        },
        "Tennis Club": {
            "description": "Tennis lessons and friendly competitions",
            "schedule": "Tuesdays and Thursdays, 3:45 PM - 5:00 PM",
            "max_participants": 8,
            "participants": ["james@mergington.edu"]
        },
        "Drama Club": {
            "description": "Theater productions and acting workshops",
            "schedule": "Mondays and Thursdays, 4:00 PM - 5:30 PM",
            "max_participants": 25,
            "participants": ["isabella@mergington.edu", "lucas@mergington.edu"]
        },
        "Art Studio": {
            "description": "Painting, drawing, and visual arts exploration",
            "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 18,
            "participants": ["maya@mergington.edu"]
        },
        "Debate Team": {
            "description": "Competitive debate and public speaking skills",
            "schedule": "Tuesdays, 3:30 PM - 5:00 PM",
            "max_participants": 10,
            "participants": ["ryan@mergington.edu", "sophia@mergington.edu"]
        },
        "Robotics Club": {
            "description": "Build and program robots for competitions",
            "schedule": "Wednesdays and Fridays, 4:00 PM - 5:45 PM",
            "max_participants": 14,
            "participants": ["noah@mergington.edu"]
        },
    }
    
    # Clear current activities and reset to original
    activities.clear()
    activities.update(original_activities)
    
    yield
    
    # Reset after test
    activities.clear()
    activities.update(original_activities)


class TestGetActivities:
    """Test cases for GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert len(data) == 9
    
    def test_get_activities_contains_required_fields(self, client):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_details in data.items():
            assert "description" in activity_details
            assert "schedule" in activity_details
            assert "max_participants" in activity_details
            assert "participants" in activity_details
    
    def test_get_activities_participants_is_list(self, client):
        """Test that participants field is a list"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_details in data.items():
            assert isinstance(activity_details["participants"], list)


class TestSignupEndpoint:
    """Test cases for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_new_participant_success(self, client):
        """Test successful signup of a new participant"""
        response = client.post(
            "/activities/Chess Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Signed up" in data["message"]
        assert "newstudent@mergington.edu" in data["message"]
        
        # Verify participant was added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "newstudent@mergington.edu" in activities_data["Chess Club"]["participants"]
    
    def test_signup_duplicate_participant_fails(self, client):
        """Test that signing up duplicate participant fails"""
        response = client.post(
            "/activities/Chess Club/signup?email=michael@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "already signed up" in data["detail"]
    
    def test_signup_nonexistent_activity_fails(self, client):
        """Test that signing up for non-existent activity fails"""
        response = client.post(
            "/activities/Nonexistent Activity/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_signup_full_activity_fails(self, client):
        """Test that signing up for full activity fails"""
        # Tennis Club has max 8 participants with only 1 current
        # Add 7 more to fill it
        for i in range(7):
            client.post(f"/activities/Tennis Club/signup?email=student{i}@mergington.edu")
        
        # Try to add one more (should fail)
        response = client.post(
            "/activities/Tennis Club/signup?email=overflow@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "full" in data["detail"]
    
    def test_signup_multiple_different_activities(self, client):
        """Test signing up same student for multiple activities"""
        email = "versatile@mergington.edu"
        
        # Sign up for first activity
        response1 = client.post(f"/activities/Chess Club/signup?email={email}")
        assert response1.status_code == 200
        
        # Sign up for second activity
        response2 = client.post(f"/activities/Art Studio/signup?email={email}")
        assert response2.status_code == 200
        
        # Verify in both activities
        activities_response = client.get("/activities")
        data = activities_response.json()
        assert email in data["Chess Club"]["participants"]
        assert email in data["Art Studio"]["participants"]


class TestUnregisterEndpoint:
    """Test cases for DELETE /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_existing_participant_success(self, client):
        """Test successful unregistration of a participant"""
        response = client.delete(
            "/activities/Chess Club/unregister?email=michael@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Unregistered" in data["message"]
        
        # Verify participant was removed
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "michael@mergington.edu" not in activities_data["Chess Club"]["participants"]
    
    def test_unregister_nonexistent_participant_fails(self, client):
        """Test that unregistering non-existent participant fails"""
        response = client.delete(
            "/activities/Chess Club/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "not registered" in data["detail"]
    
    def test_unregister_nonexistent_activity_fails(self, client):
        """Test that unregistering from non-existent activity fails"""
        response = client.delete(
            "/activities/Nonexistent Activity/unregister?email=someone@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_unregister_then_signup_again_succeeds(self, client):
        """Test that unregistering and signing up again works"""
        email = "michael@mergington.edu"
        activity = "Chess Club"
        
        # Unregister
        response1 = client.delete(f"/activities/{activity}/unregister?email={email}")
        assert response1.status_code == 200
        
        # Sign up again
        response2 = client.post(f"/activities/{activity}/signup?email={email}")
        assert response2.status_code == 200
        
        # Verify participant is back
        activities_response = client.get("/activities")
        data = activities_response.json()
        assert email in data[activity]["participants"]


class TestRootEndpoint:
    """Test cases for GET / endpoint"""
    
    def test_root_redirects_to_static(self, client):
        """Test that root endpoint redirects to /static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code in [301, 302, 303, 307, 308]
        assert "/static/index.html" in response.headers["location"]
