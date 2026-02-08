"""Unit tests for FastAPI app endpoints"""

import pytest


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_success(self, client):
        """Test successfully retrieving all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert len(data) == 9

    def test_get_activities_structure(self, client):
        """Test that activities have correct structure"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, details in data.items():
            assert "description" in details
            assert "schedule" in details
            assert "max_participants" in details
            assert "participants" in details
            assert isinstance(details["participants"], list)


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_success(self, client, reset_activities):
        """Test successfully signing up for an activity"""
        response = client.post(
            "/activities/Chess Club/signup?email=test@example.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "test@example.edu" in data["message"]
        assert "Chess Club" in data["message"]

    def test_signup_adds_participant(self, client, reset_activities):
        """Test that signup actually adds participant to activity"""
        client.post("/activities/Basketball Team/signup?email=new@test.edu")
        
        response = client.get("/activities")
        activities = response.json()
        assert "new@test.edu" in activities["Basketball Team"]["participants"]

    def test_signup_duplicate_student(self, client, reset_activities):
        """Test that signing up twice fails"""
        # First signup
        response1 = client.post(
            "/activities/Chess Club/signup?email=duplicate@test.edu"
        )
        assert response1.status_code == 200
        
        # Second signup
        response2 = client.post(
            "/activities/Chess Club/signup?email=duplicate@test.edu"
        )
        assert response2.status_code == 400
        data = response2.json()
        assert "already signed up" in data["detail"]

    def test_signup_nonexistent_activity(self, client, reset_activities):
        """Test signing up for a nonexistent activity"""
        response = client.post(
            "/activities/Nonexistent Club/signup?email=test@test.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_signup_multiple_students(self, client, reset_activities):
        """Test that multiple students can sign up for same activity"""
        emails = ["student1@test.edu", "student2@test.edu", "student3@test.edu"]
        
        for email in emails:
            response = client.post(
                f"/activities/Tennis Club/signup?email={email}"
            )
            assert response.status_code == 200
        
        # Verify all signed up
        response = client.get("/activities")
        participants = response.json()["Tennis Club"]["participants"]
        for email in emails:
            assert email in participants


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""

    def test_unregister_success(self, client, reset_activities):
        """Test successfully unregistering from an activity"""
        # First signup
        client.post("/activities/Art Studio/signup?email=artist@test.edu")
        
        # Then unregister
        response = client.delete(
            "/activities/Art Studio/unregister?email=artist@test.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Unregistered" in data["message"]

    def test_unregister_removes_participant(self, client, reset_activities):
        """Test that unregister actually removes participant"""
        # Signup
        client.post("/activities/Drama Club/signup?email=actor@test.edu")
        
        # Unregister
        client.delete("/activities/Drama Club/unregister?email=actor@test.edu")
        
        # Verify removed
        response = client.get("/activities")
        participants = response.json()["Drama Club"]["participants"]
        assert "actor@test.edu" not in participants

    def test_unregister_nonexistent_activity(self, client, reset_activities):
        """Test unregistering from nonexistent activity"""
        response = client.delete(
            "/activities/Fake Club/unregister?email=test@test.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_unregister_not_registered_student(self, client, reset_activities):
        """Test unregistering a student who wasn't registered"""
        response = client.delete(
            "/activities/Science Club/unregister?email=notregistered@test.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "not registered" in data["detail"]

    def test_unregister_original_participant(self, client, reset_activities):
        """Test unregistering an original participant"""
        # Original participant in Science Club is "grace@mergington.edu"
        response = client.delete(
            "/activities/Science Club/unregister?email=grace@mergington.edu"
        )
        assert response.status_code == 200
        
        # Verify removed
        response = client.get("/activities")
        participants = response.json()["Science Club"]["participants"]
        assert "grace@mergington.edu" not in participants


class TestIntegration:
    """Integration tests for complete workflows"""

    def test_complete_signup_workflow(self, client, reset_activities):
        """Test complete signup workflow"""
        # Get initial state
        response1 = client.get("/activities")
        initial_count = len(response1.json()["Debate Team"]["participants"])
        
        # Sign up
        response2 = client.post(
            "/activities/Debate Team/signup?email=newdebater@test.edu"
        )
        assert response2.status_code == 200
        
        # Verify update
        response3 = client.get("/activities")
        new_count = len(response3.json()["Debate Team"]["participants"])
        assert new_count == initial_count + 1

    def test_signup_then_unregister_workflow(self, client, reset_activities):
        """Test signup followed by unregister"""
        email = "tempstudent@test.edu"
        
        # Sign up
        client.post(f"/activities/Programming Class/signup?email={email}")
        
        response = client.get("/activities")
        assert email in response.json()["Programming Class"]["participants"]
        
        # Unregister
        client.delete(f"/activities/Programming Class/unregister?email={email}")
        
        response = client.get("/activities")
        assert email not in response.json()["Programming Class"]["participants"]
