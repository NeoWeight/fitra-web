from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()

REGISTER_URL = '/api/v1/auth/register/'
LOGIN_URL = '/api/v1/auth/login/'
TOKEN_REFRESH_URL = '/api/v1/auth/token/refresh/'
ME_URL = '/api/v1/users/me/'


def profile_url(username):
    return f'/api/v1/users/{username}/'


class RegisterTests(APITestCase):
    def test_register_success(self):
        data = {'email': 'test@example.com', 'username': 'testuser', 'password': 'strongpass123'}
        response = self.client.post(REGISTER_URL, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email='test@example.com')
        self.assertTrue(hasattr(user, 'profile'))

    def test_register_duplicate_email(self):
        User.objects.create_user(email='test@example.com', username='existing', password='pass123456')
        data = {'email': 'test@example.com', 'username': 'newuser', 'password': 'strongpass123'}
        response = self.client.post(REGISTER_URL, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_duplicate_username(self):
        User.objects.create_user(email='other@example.com', username='testuser', password='pass123456')
        data = {'email': 'new@example.com', 'username': 'testuser', 'password': 'strongpass123'}
        response = self.client.post(REGISTER_URL, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_missing_fields(self):
        response = self.client.post(REGISTER_URL, {'email': 'test@example.com'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_password_too_short(self):
        data = {'email': 'test@example.com', 'username': 'testuser', 'password': 'short'}
        response = self.client.post(REGISTER_URL, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LoginTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com', username='testuser', password='strongpass123'
        )

    def test_login_success(self):
        response = self.client.post(LOGIN_URL, {'email': 'test@example.com', 'password': 'strongpass123'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_wrong_password(self):
        response = self.client.post(LOGIN_URL, {'email': 'test@example.com', 'password': 'wrongpass'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_nonexistent_email(self):
        response = self.client.post(LOGIN_URL, {'email': 'nobody@example.com', 'password': 'pass'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_refresh(self):
        login = self.client.post(LOGIN_URL, {'email': 'test@example.com', 'password': 'strongpass123'})
        response = self.client.post(TOKEN_REFRESH_URL, {'refresh': login.data['refresh']})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)


class MeViewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com', username='testuser', password='strongpass123'
        )

    def test_me_authenticated(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(ME_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'test@example.com')
        self.assertEqual(response.data['username'], 'testuser')
        self.assertIn('profile', response.data)

    def test_me_unauthenticated(self):
        response = self.client.get(ME_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_patch_bio(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(ME_URL, {'profile': {'bio': 'Hello world'}}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.bio, 'Hello world')

    def test_me_patch_avatar(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(ME_URL, {'profile': {'avatar_url': 'https://example.com/avatar.jpg'}}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.avatar_url, 'https://example.com/avatar.jpg')

    def test_me_patch_first_name(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(ME_URL, {'first_name': 'Neo'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Neo')

    def test_me_put_not_allowed(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.put(ME_URL, {'username': 'newname', 'email': 'x@x.com'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class UserProfileViewTests(APITestCase):
    def setUp(self):
        self.public_user = User.objects.create_user(
            email='public@example.com', username='publicuser', password='pass123456'
        )
        self.private_user = User.objects.create_user(
            email='private@example.com', username='privateuser', password='pass123456'
        )
        self.private_user.profile.is_public = False
        self.private_user.profile.save()

    def test_public_profile_visible_unauthenticated(self):
        response = self.client.get(profile_url('publicuser'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'publicuser')

    def test_private_profile_hidden_from_unauthenticated(self):
        response = self.client.get(profile_url('privateuser'))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_private_profile_hidden_from_other_user(self):
        self.client.force_authenticate(user=self.public_user)
        response = self.client.get(profile_url('privateuser'))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_private_profile_visible_to_owner(self):
        self.client.force_authenticate(user=self.private_user)
        response = self.client.get(profile_url('privateuser'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_nonexistent_user(self):
        response = self.client.get(profile_url('nobody'))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
