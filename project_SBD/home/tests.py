from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse

from .models import Consultation

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
