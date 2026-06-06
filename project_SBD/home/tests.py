from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import (
    Consultation,
    EmailOTPSettings,
    PasswordOTP,
    Product,
    ProductCategory,
    SiteBrandSettings,
    SpecializedServiceContent,
)

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


class SpecializedServiceContentTests(TestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(
            username="service_staff",
            password="StrongPass123!",
            is_staff=True,
        )

    def test_public_pages_only_show_the_requested_sector(self):
        industrial = SpecializedServiceContent.objects.create(
            sector=SpecializedServiceContent.INDUSTRIAL,
            title="Nha may",
            content="Noi dung cong nghiep",
        )
        SpecializedServiceContent.objects.create(
            sector=SpecializedServiceContent.CIVIL,
            title="Nha o",
            content="Noi dung dan dung",
        )

        response = self.client.get(reverse("industrial"))

        self.assertContains(response, industrial.title)
        self.assertNotContains(response, "Nha o")
        self.assertContains(
            self.client.get(reverse("industrial_detail", args=[industrial.id])),
            industrial.content,
        )

    def test_staff_can_create_update_and_delete_sector_content(self):
        self.client.force_login(self.staff_user)

        self.assertEqual(self.client.get(reverse("energy_green_list")).status_code, 200)
        self.assertEqual(self.client.get(reverse("energy_green_add")).status_code, 200)

        create_response = self.client.post(
            reverse("energy_green_add"),
            {
                "title": "Dien mat troi",
                "summary": "Giai phap xanh",
                "content": "Noi dung chi tiet",
            },
        )
        item = SpecializedServiceContent.objects.get(title="Dien mat troi")
        self.assertRedirects(create_response, reverse("energy_green_list"))
        self.assertEqual(item.sector, SpecializedServiceContent.ENERGY_GREEN)

        update_response = self.client.post(
            reverse("energy_green_edit", args=[item.id]),
            {
                "title": "Nang luong mat troi",
                "summary": "Giai phap xanh",
                "content": "Noi dung da cap nhat",
            },
        )
        self.assertRedirects(update_response, reverse("energy_green_list"))
        item.refresh_from_db()
        self.assertEqual(item.title, "Nang luong mat troi")

        delete_response = self.client.get(
            reverse("energy_green_delete", args=[item.id])
        )
        self.assertRedirects(delete_response, reverse("energy_green_list"))
        self.assertFalse(SpecializedServiceContent.objects.filter(id=item.id).exists())

    def test_non_staff_cannot_access_management_pages(self):
        response = self.client.get(reverse("civil_list"))
        self.assertRedirects(response, f"/login/?next={reverse('civil_list')}")


class ManagementNavigationTests(TestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(
            username="navigation_staff",
            password="StrongPass123!",
            is_staff=True,
        )
        self.admin_user = User.objects.create_superuser(
            username="navigation_admin",
            password="StrongPass123!",
            email="navigation_admin@example.com",
        )

    def test_staff_sees_compact_navigation_on_list_and_form_pages(self):
        self.client.force_login(self.staff_user)

        for url_name in ("dashboard", "product_add", "service_add"):
            response = self.client.get(reverse(url_name))
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "Điều hướng quản trị")
            self.assertContains(response, reverse("industrial_list"))
            self.assertContains(response, reverse("contact_info_list"))

        self.assertNotContains(response, "Cài đặt hệ thống")

    def test_admin_sees_system_navigation(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(reverse("system_settings"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Điều hướng quản trị")
        self.assertContains(response, "Cài đặt hệ thống")
        self.assertContains(response, reverse("staff_account_add"))


class SearchFunctionPermissionTests(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(
            username="search_customer",
            password="StrongPass123!",
        )
        self.staff_user = User.objects.create_user(
            username="search_staff",
            password="StrongPass123!",
            is_staff=True,
        )
        self.admin_user = User.objects.create_superuser(
            username="search_admin",
            password="StrongPass123!",
            email="search_admin@example.com",
        )

    def test_guest_and_customer_cannot_see_management_functions(self):
        guest_response = self.client.get(reverse("search"), {"q": "san pham"})
        self.assertNotContains(guest_response, "Chức Năng Quản Trị")
        self.assertNotContains(guest_response, "Quản lý sản phẩm")

        self.client.force_login(self.customer)
        customer_response = self.client.get(reverse("search"), {"q": "san pham"})
        self.assertNotContains(customer_response, "Chức Năng Quản Trị")
        self.assertNotContains(customer_response, "Quản lý sản phẩm")

    def test_staff_can_search_management_functions_without_accents(self):
        self.client.force_login(self.staff_user)

        response = self.client.get(reverse("search"), {"q": "san pham"})

        self.assertContains(response, "Chức Năng Quản Trị")
        self.assertContains(response, "Quản lý sản phẩm")
        self.assertContains(response, reverse("product_list"))
        self.assertContains(response, reverse("product_add"))

    def test_system_functions_are_only_visible_to_admin(self):
        self.client.force_login(self.staff_user)
        staff_response = self.client.get(reverse("search"), {"q": "cai dat"})
        self.assertNotContains(staff_response, "Cài đặt hệ thống")

        self.client.force_login(self.admin_user)
        admin_response = self.client.get(reverse("search"), {"q": "cai dat"})
        self.assertContains(admin_response, "Cài đặt hệ thống")
        self.assertContains(admin_response, reverse("system_settings"))


class FaviconSettingsTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username="favicon_admin",
            password="StrongPass123!",
            email="favicon_admin@example.com",
        )

    def test_base_uses_custom_favicon(self):
        config = SiteBrandSettings.get_solo()
        config.favicon_image = "branding/favicon/custom.png"
        config.save()

        response = self.client.get(reverse("home"))

        self.assertContains(response, 'href="/media/branding/favicon/custom.png"')

    def test_base_falls_back_to_logo_image(self):
        config = SiteBrandSettings.get_solo()
        config.logo_image = "branding/logo.png"
        config.favicon_image = None
        config.save()

        response = self.client.get(reverse("home"))

        self.assertContains(response, 'href="/media/branding/logo.png"')

    def test_admin_can_access_favicon_field(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(reverse("system_settings"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Icon đầu trang / tab trình duyệt (favicon)")
        self.assertContains(response, 'name="favicon_image"')
        self.assertContains(response, 'id="favicon-settings"')

    def test_admin_can_search_direct_favicon_link(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(reverse("search"), {"q": "favicon"})

        self.assertContains(response, "Icon tab trình duyệt")
        self.assertContains(
            response,
            f'{reverse("system_settings")}#favicon-settings',
        )


class AuthenticationLogoTests(TestCase):
    def test_login_and_register_use_preloader_image(self):
        config = SiteBrandSettings.get_solo()
        config.preloader_image = "branding/preloader/auth-logo.png"
        config.save()

        expected_url = "/media/branding/preloader/auth-logo.png"
        for url_name in ("login", "register"):
            response = self.client.get(reverse(url_name))
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, expected_url)


@override_settings(
    STORAGES={
        "default": {
            "BACKEND": "django.core.files.storage.memory.InMemoryStorage",
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }
)
class ContentGalleryTests(TestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(
            username="gallery_staff",
            password="StrongPass123!",
            is_staff=True,
        )
        self.category = ProductCategory.objects.create(name="Thiết bị")
        self.client.force_login(self.staff_user)

    @staticmethod
    def image_file(name):
        return SimpleUploadedFile(name, b"test-image-content", content_type="image/jpeg")

    def test_product_supports_multiple_images_and_gallery_deletion(self):
        response = self.client.post(
            reverse("product_add"),
            {
                "name": "Sản phẩm nhiều ảnh",
                "description": "Mô tả",
                "category": self.category.id,
                "image_mode": "multiple",
                "multiple_images": [
                    self.image_file("cover.jpg"),
                    self.image_file("detail-1.jpg"),
                    self.image_file("detail-2.jpg"),
                ],
            },
        )

        self.assertRedirects(response, reverse("product_list"))
        product = Product.objects.get(name="Sản phẩm nhiều ảnh")
        self.assertTrue(product.image.name.endswith("cover.jpg"))
        self.assertEqual(product.image_mode, "multiple")
        self.assertEqual(product.gallery_images.count(), 2)

        detail_response = self.client.get(reverse("product_detail", args=[product.id]))
        self.assertContains(detail_response, "data-content-gallery")
        self.assertContains(detail_response, "data-gallery-slide", count=3)
        self.assertContains(detail_response, "data-lightbox-zoom-in")
        self.assertContains(detail_response, "data-lightbox-fullscreen")

        gallery_image = product.gallery_images.first()
        response = self.client.post(
            reverse("product_edit", args=[product.id]),
            {
                "name": product.name,
                "description": product.description,
                "category": self.category.id,
                "image_mode": "multiple",
                "delete_gallery_images": [gallery_image.id],
            },
        )

        self.assertRedirects(response, reverse("product_list"))
        self.assertEqual(product.gallery_images.count(), 1)

    def test_single_image_mode_replaces_cover_but_preserves_gallery(self):
        product = Product.objects.create(
            name="Sản phẩm chuyển chế độ",
            category=self.category,
            image="products/cover.jpg",
            image_mode="multiple",
        )
        product.gallery_images.create(image="galleries/product/detail.jpg")

        response = self.client.post(
            reverse("product_edit", args=[product.id]),
            {
                "name": product.name,
                "description": "",
                "category": self.category.id,
                "image_mode": "single",
                "single_image": self.image_file("new-cover.jpg"),
            },
        )

        self.assertRedirects(response, reverse("product_list"))
        product.refresh_from_db()
        self.assertEqual(product.image_mode, "single")
        self.assertTrue(product.image.name.endswith("new-cover.jpg"))
        self.assertEqual(product.gallery_images.count(), 1)

    def test_editing_multiple_images_appends_files_and_can_select_cover(self):
        product = Product.objects.create(
            name="Sản phẩm bổ sung ảnh",
            category=self.category,
            image="products/original-cover.jpg",
            image_mode="multiple",
        )
        existing_gallery = product.gallery_images.create(
            image="galleries/product/existing.jpg"
        )

        response = self.client.post(
            reverse("product_edit", args=[product.id]),
            {
                "name": product.name,
                "description": "",
                "category": self.category.id,
                "image_mode": "multiple",
                "cover_image": "primary",
                "multiple_images": [
                    self.image_file("added-1.jpg"),
                    self.image_file("added-2.jpg"),
                ],
            },
        )

        self.assertRedirects(response, reverse("product_list"))
        product.refresh_from_db()
        self.assertTrue(product.image.name.endswith("original-cover.jpg"))
        self.assertEqual(product.gallery_images.count(), 3)

        response = self.client.post(
            reverse("product_edit", args=[product.id]),
            {
                "name": product.name,
                "description": "",
                "category": self.category.id,
                "image_mode": "multiple",
                "cover_image": f"gallery:{existing_gallery.id}",
            },
        )

        self.assertRedirects(response, reverse("product_list"))
        product.refresh_from_db()
        existing_gallery.refresh_from_db()
        self.assertTrue(product.image.name.endswith("existing.jpg"))
        self.assertTrue(existing_gallery.image.name.endswith("original-cover.jpg"))
        self.assertEqual(product.gallery_images.count(), 3)

    def test_product_form_displays_and_selects_category(self):
        add_response = self.client.get(reverse("product_add"))
        self.assertContains(add_response, 'name="multiple_images"')
        self.assertContains(add_response, "multiple")
        self.assertContains(
            add_response,
            f'<option value="{self.category.id}">{self.category.name}</option>',
            html=True,
        )

        product = Product.objects.create(
            name="Sản phẩm có danh mục",
            category=self.category,
            image="products/form-cover.jpg",
        )
        edit_response = self.client.get(reverse("product_edit", args=[product.id]))
        self.assertContains(edit_response, 'name="cover_image"')
        self.assertContains(
            edit_response,
            (
                f'<option value="{self.category.id}" selected>'
                f"{self.category.name}</option>"
            ),
            html=True,
        )
