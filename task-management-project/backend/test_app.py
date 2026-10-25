import unittest
from unittest.mock import patch
from app import app


class TaskApiTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_create_requires_json_object(self):
        response = self.client.post("/api/tasks", data="not json", content_type="text/plain")
        self.assertEqual(response.status_code, 400)

    def test_create_requires_title(self):
        response = self.client.post("/api/tasks", json={"description": "Missing title"})
        self.assertEqual(response.status_code, 400)

    def test_create_rejects_invalid_status(self):
        response = self.client.post("/api/tasks", json={"title": "Test", "status": "unknown"})
        self.assertEqual(response.status_code, 400)

    @patch("app.fetch_tasks", return_value=[{"id": 1, "title": "Example"}])
    def test_list_tasks(self, mocked_fetch):
        response = self.client.get("/api/tasks")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()[0]["title"], "Example")
        mocked_fetch.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
