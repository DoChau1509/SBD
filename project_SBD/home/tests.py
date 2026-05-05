from django.core import mail
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse

from .models import Consultation, EmailOTPSettings, PasswordOTP

User = get_user_model()


class ConsultationStatusFlowTests(TestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(
            username="staff",
            password="StrongPass123!",
            is_staff=True,
        )
        self.customer = User.objects.create_user(
            username="customer",
            password="StrongPass123!",
            email="customer@example.com",
        )
        self.consultation = Consultation.objects.create(
            user=self.customer,
            full_name="Nguyen Van A",
            phone="0901234567",
            subject="Tu van nha pho",
            status="processing",
        )

    def test_cannot_move_consultation_status_backwards(self):
        self.client.force_login(self.staff_user)

        response = self.client.post(
            reverse("consultation_detail", args=[self.consultation.id]),
            {"status": "pending"},
            follow=True,
        )

        self.consultation.refresh_from_db()
        self.assertEqual(self.consultation.status, "processing")
        messages = [message.message for message in get_messages(response.wsgi_request)]
        self.assertIn("Không thể cập nhật trạng thái lùi về bước trước.", messages)

    def test_can_move_consultation_status_forward(self):
        self.client.force_login(self.staff_user)

        response = self.client.post(
            reverse("consultation_detail", args=[self.consultation.id]),
            {"status": "done"},
            follow=True,
        )

        self.consultation.refresh_from_db()
        self.assertEqual(self.consultation.status, "done")
        self.assertEqual(self.consultation.handled_by, self.staff_user)
        messages = [message.message for message in get_messages(response.wsgi_request)]
        self.assertIn("Đã cập nhật trạng thái yêu cầu tư vấn.", messages)


class UserRegistrationTests(TestCase):
    def test_register_creates_user_with_profile_fields(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "newuser",
                "first_name": "Nguyen",
                "last_name": "Van B",
                "email": "newuser@example.com",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
            follow=True,
        )

        user = User.objects.get(username="newuser")
        self.assertEqual(user.first_name, "Nguyen")
        self.assertEqual(user.last_name, "Van B")
        self.assertEqual(user.email, "newuser@example.com")
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_register_rejects_duplicate_email(self):
        User.objects.create_user(
            username="existing",
            password="StrongPass123!",
            email="existing@example.com",
        )

        response = self.client.post(
            reverse("register"),
            {
                "username": "anotheruser",
                "first_name": "Tran",
                "last_name": "Thi C",
                "email": "existing@example.com",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
        )

        self.assertContains(response, "Email này đã được sử dụng.")
        self.assertFalse(User.objects.filter(username="anotheruser").exists())


class StaffAccountManagementTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username="admin",
            password="StrongPass123!",
            email="admin@example.com",
        )
        self.staff_user = User.objects.create_user(
            username="staffmember",
            password="StrongPass123!",
            email="staffmember@example.com",
            is_staff=True,
        )

    def test_admin_can_create_staff_account(self):
        self.client.force_login(self.admin_user)

        response = self.client.post(
            reverse("staff_account_add"),
            {
                "username": "newstaff",
                "first_name": "Pham",
                "last_name": "Nhan Su",
                "email": "newstaff@example.com",
                "is_active": "on",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
            follow=True,
        )

        created_user = User.objects.get(username="newstaff")
        self.assertTrue(created_user.is_staff)
        self.assertFalse(created_user.is_superuser)
        self.assertTrue(created_user.is_active)
        self.assertContains(response, "Đã tạo tài khoản staff mới.")

    def test_staff_user_cannot_access_staff_account_management(self):
        self.client.force_login(self.staff_user)

        response = self.client.get(reverse("staff_account_list"), follow=True)

        self.assertRedirects(response, reverse("dashboard"))
        messages = [message.message for message in get_messages(response.wsgi_request)]
        self.assertIn("Chỉ quản trị viên mới có quyền quản lý tài khoản.", messages)


class PasswordOTPFlowTests(TestCase):
    def setUp(self):
        EmailOTPSettings.objects.create(
            sender_name="SBD OTP",
            sender_email="no-reply@example.com",
            smtp_host="localhost",
            smtp_port=25,
            smtp_username="",
            smtp_password="",
            use_tls=False,
            use_ssl=False,
        )
        self.user = User.objects.create_user(
            username="otpuser",
            password="OldStrongPass123!",
            email="otpuser@example.com",
        )

    def test_forgot_password_flow_resets_password_with_otp(self):
        response = self.client.post(
            reverse("forgot_password"),
            {"identifier": "otpuser"},
            follow=True,
        )

        self.assertRedirects(response, reverse("forgot_password_verify"))
        self.assertEqual(len(mail.outbox), 1)

        otp = PasswordOTP.objects.get(user=self.user, purpose="forgot_password")
        verify_response = self.client.post(
            reverse("forgot_password_verify"),
            {
                "otp_code": otp.code,
                "password1": "NewStrongPass123!",
                "password2": "NewStrongPass123!",
            },
            follow=True,
        )

        self.assertRedirects(verify_response, reverse("login"))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewStrongPass123!"))

    def test_change_password_flow_requires_login_and_otp(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("change_password_request"),
            {"current_password": "OldStrongPass123!"},
            follow=True,
        )

        self.assertRedirects(response, reverse("change_password_verify"))
        self.assertEqual(len(mail.outbox), 1)

        otp = PasswordOTP.objects.get(user=self.user, purpose="change_password")
        verify_response = self.client.post(
            reverse("change_password_verify"),
            {
                "otp_code": otp.code,
                "password1": "AnotherStrongPass123!",
                "password2": "AnotherStrongPass123!",
            },
            follow=True,
        )

        self.assertRedirects(verify_response, reverse("login"))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("AnotherStrongPass123!"))
