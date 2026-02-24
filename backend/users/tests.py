from django.test import TestCase
from django.test import override_settings
from django.urls import reverse
from django.contrib.auth.models import User
from django.core import mail


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
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

	def test_register_sends_otp_and_creates_inactive_user(self):
		response = self.client.post(reverse('register'), {
			'username': 'otpuser',
			'email': 'otp@example.com',
			'password': 'StrongPass123!',
			'password2': 'StrongPass123!',
		})
		self.assertRedirects(response, reverse('verify_email_otp'))

		created_user = User.objects.get(username='otpuser')
		self.assertFalse(created_user.is_active)
		self.assertEqual(len(mail.outbox), 1)

	def test_verify_correct_otp_activates_user(self):
		self.client.post(reverse('register'), {
			'username': 'verifyotp',
			'email': 'verifyotp@example.com',
			'password': 'StrongPass123!',
			'password2': 'StrongPass123!',
		})

		session = self.client.session
		otp = session['registration_otp']['otp']

		response = self.client.post(reverse('verify_email_otp'), {'otp': otp})
		self.assertRedirects(response, reverse('login'))

		verified_user = User.objects.get(username='verifyotp')
		self.assertTrue(verified_user.is_active)

	def test_verify_wrong_otp_keeps_user_inactive(self):
		self.client.post(reverse('register'), {
			'username': 'wrongotp',
			'email': 'wrongotp@example.com',
			'password': 'StrongPass123!',
			'password2': 'StrongPass123!',
		})

		response = self.client.post(reverse('verify_email_otp'), {'otp': '000000'})
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Invalid OTP')

		pending_user = User.objects.get(username='wrongotp')
		self.assertFalse(pending_user.is_active)

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
