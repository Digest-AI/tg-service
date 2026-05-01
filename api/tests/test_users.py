from django.conf import settings
from rest_framework import status
from rest_framework.test import APITestCase

from api.models import User

SECRET = settings.SERVICE_SECRET


class UserListCreateTests(APITestCase):
    url = "/api/users/"

    def setUp(self):
        self.client.credentials(HTTP_X_SERVICE_SECRET=SECRET)

    def test_list_empty(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), [])

    def test_list_returns_all_users(self):
        User.objects.create(public_id="uid-1", username="user1", telegram_id="111")
        User.objects.create(public_id="uid-2", username="user2", telegram_id="222")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 2)

    def test_create_user(self):
        payload = {"publicId": "uid-1", "username": "user1", "telegramId": "123456789"}
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertEqual(data["publicId"], "uid-1")
        self.assertEqual(data["username"], "user1")
        self.assertEqual(data["telegramId"], "123456789")
        self.assertEqual(User.objects.count(), 1)

    def test_create_user_duplicate_username(self):
        User.objects.create(public_id="uid-existing", username="user1", telegram_id="111")
        payload = {"publicId": "uid-new", "username": "user1", "telegramId": "222"}
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_user_duplicate_telegram_id(self):
        User.objects.create(public_id="uid-existing", username="user1", telegram_id="111")
        payload = {"publicId": "uid-new", "username": "user2", "telegramId": "111"}
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_user_missing_fields(self):
        response = self.client.post(self.url, {"username": "user1"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserDetailTests(APITestCase):
    def setUp(self):
        self.client.credentials(HTTP_X_SERVICE_SECRET=SECRET)
        self.user = User.objects.create(
            public_id="uid-1",
            username="user1",
            telegram_id="123456789",
        )
        self.url = f"/api/users/{self.user.pk}/"

    def test_get_user(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["publicId"], "uid-1")
        self.assertEqual(data["username"], "user1")
        self.assertEqual(data["telegramId"], "123456789")

    def test_get_user_not_found(self):
        response = self.client.get("/api/users/9999/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patch_username(self):
        response = self.client.patch(self.url, {"username": "updated"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["username"], "updated")
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "updated")

    def test_patch_public_id(self):
        response = self.client.patch(self.url, {"publicId": "uid-new"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["publicId"], "uid-new")

    def test_delete_user(self):
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(pk=self.user.pk).exists())
