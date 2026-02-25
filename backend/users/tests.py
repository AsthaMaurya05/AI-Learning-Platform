from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User


class AuthenticationFlowTests(TestCase):
	def setUp(self):
		self.password = 'StrongPass123!'
		self.user = User.objects.create_user(
			username='testuser',
			email='test@example.com',
			password=self.password,
		)

	def test_register_rejects_weak_password(self):
		response = self.client.post(reverse('register'), {
			'username': 'newuser',
			'email': 'new@example.com',
			'password': '12345678',
			'password2': '12345678',
		})
		self.assertEqual(response.status_code, 200)
		self.assertFalse(User.objects.filter(username='newuser').exists())

	def test_register_creates_active_user_and_redirects_login(self):
		response = self.client.post(reverse('register'), {
			'username': 'otpuser',
			'email': 'otp@example.com',
			'password': 'StrongPass123!',
			'password2': 'StrongPass123!',
		})
		self.assertRedirects(response, reverse('login'))

		created_user = User.objects.get(username='otpuser')
		self.assertTrue(created_user.is_active)

	def test_login_works_immediately_after_registration(self):
		self.client.post(reverse('register'), {
			'username': 'verifyotp',
			'email': 'verifyotp@example.com',
			'password': 'StrongPass123!',
			'password2': 'StrongPass123!',
		})

		response = self.client.post(reverse('login'), {
			'username': 'verifyotp',
			'password': 'StrongPass123!',
		})
		self.assertRedirects(response, reverse('dashboard'))

		verified_user = User.objects.get(username='verifyotp')
		self.assertTrue(verified_user.is_active)

	def test_login_with_safe_next_redirects_to_internal_path(self):
		response = self.client.post(
			f"{reverse('login')}?next={reverse('dashboard')}",
			{
				'username': self.user.username,
				'password': self.password,
				'next': reverse('dashboard'),
			},
		)
		self.assertRedirects(response, reverse('dashboard'))

	def test_login_with_external_next_falls_back_to_dashboard(self):
		response = self.client.post(
			f"{reverse('login')}?next=https://evil.example.com",
			{
				'username': self.user.username,
				'password': self.password,
				'next': 'https://evil.example.com',
			},
		)
		self.assertRedirects(response, reverse('dashboard'))

	def test_logout_requires_post(self):
		self.client.login(username=self.user.username, password=self.password)
		response = self.client.get(reverse('logout'))
		self.assertEqual(response.status_code, 405)

	def test_logout_post_logs_user_out(self):
		self.client.login(username=self.user.username, password=self.password)
		response = self.client.post(reverse('logout'))
		self.assertRedirects(response, reverse('login'))
