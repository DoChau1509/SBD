from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.password_validation import validate_password

from .models import EmailOTPSettings, SiteBrandSettings

User = get_user_model()


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Tên đăng nhập",
                "autocomplete": "username",
            }
        )
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Mật khẩu",
                "autocomplete": "current-password",
            }
        )
    )


class UserRegistrationForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Ví dụ: Nguyễn",
                "autocomplete": "family-name",
            }
        ),
    )
    last_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Ví dụ: Văn A",
                "autocomplete": "given-name",
            }
        ),
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "example@email.com",
                "autocomplete": "email",
            }
        ),
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "last_name", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update(
            {
                "class": "form-control",
                "placeholder": "Tên đăng nhập",
                "autocomplete": "username",
            }
        )
        self.fields["username"].help_text = "Chỉ gồm chữ, số và @/./+/-/_."
        self.fields["email"].help_text = "Email được dùng để nhận phản hồi và khôi phục thông tin sau này."
        self.fields["password1"].widget.attrs.update(
            {
                "class": "form-control",
                "placeholder": "Mật khẩu",
                "autocomplete": "new-password",
            }
        )
        self.fields["password2"].widget.attrs.update(
            {
                "class": "form-control",
                "placeholder": "Nhập lại mật khẩu",
                "autocomplete": "new-password",
            }
        )

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        if not email:
            raise forms.ValidationError("Vui lòng nhập email.")
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Email này đã được sử dụng.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = (self.cleaned_data.get("first_name") or "").strip()
        user.last_name = (self.cleaned_data.get("last_name") or "").strip()
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


class StaffAccountCreationForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Họ",
                "autocomplete": "family-name",
            }
        ),
    )
    last_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Tên",
                "autocomplete": "given-name",
            }
        ),
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "staff@example.com",
                "autocomplete": "email",
            }
        ),
    )
    is_active = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        label="Kích hoạt tài khoản",
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "is_active",
            "password1",
            "password2",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update(
            {
                "class": "form-control",
                "placeholder": "Tên đăng nhập",
                "autocomplete": "username",
            }
        )
        self.fields["password1"].widget.attrs.update(
            {
                "class": "form-control",
                "placeholder": "Mật khẩu",
                "autocomplete": "new-password",
            }
        )
        self.fields["password2"].widget.attrs.update(
            {
                "class": "form-control",
                "placeholder": "Nhập lại mật khẩu",
                "autocomplete": "new-password",
            }
        )

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        if not email:
            raise forms.ValidationError("Vui lòng nhập email.")
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Email này đã được sử dụng.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = (self.cleaned_data.get("first_name") or "").strip()
        user.last_name = (self.cleaned_data.get("last_name") or "").strip()
        user.email = self.cleaned_data["email"]
        user.is_staff = True
        user.is_superuser = False
        user.is_active = self.cleaned_data.get("is_active", True)
        if commit:
            user.save()
        return user


class StaffAccountUpdateForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Họ",
                "autocomplete": "family-name",
            }
        ),
    )
    last_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Tên",
                "autocomplete": "given-name",
            }
        ),
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "staff@example.com",
                "autocomplete": "email",
            }
        ),
    )
    is_active = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        label="Kích hoạt tài khoản",
    )

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "is_active")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update(
            {
                "class": "form-control",
                "placeholder": "Tên đăng nhập",
                "autocomplete": "username",
            }
        )

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        if not email:
            raise forms.ValidationError("Vui lòng nhập email.")
        if (
            User.objects.filter(email__iexact=email)
            .exclude(pk=self.instance.pk)
            .exists()
        ):
            raise forms.ValidationError("Email này đã được sử dụng.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = (self.cleaned_data.get("first_name") or "").strip()
        user.last_name = (self.cleaned_data.get("last_name") or "").strip()
        user.email = self.cleaned_data["email"]
        user.is_staff = True
        user.is_superuser = False
        if commit:
            user.save()
        return user


class ForgotPasswordRequestForm(forms.Form):
    identifier = forms.CharField(
        label="Tên đăng nhập hoặc email",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Nhập tên đăng nhập hoặc email",
                "autocomplete": "username",
            }
        ),
    )


class OTPPasswordResetForm(forms.Form):
    otp_code = forms.CharField(
        label="Mã OTP",
        max_length=6,
        min_length=6,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Nhập mã OTP gồm 6 số",
                "inputmode": "numeric",
                "autocomplete": "one-time-code",
            }
        ),
    )
    password1 = forms.CharField(
        label="Mật khẩu mới",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Mật khẩu mới",
                "autocomplete": "new-password",
            }
        ),
    )
    password2 = forms.CharField(
        label="Nhập lại mật khẩu mới",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Nhập lại mật khẩu mới",
                "autocomplete": "new-password",
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

    def clean_otp_code(self):
        return (self.cleaned_data.get("otp_code") or "").strip()

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            self.add_error("password2", "Mật khẩu nhập lại không khớp.")

        if password1 and self.user:
            try:
                validate_password(password1, self.user)
            except forms.ValidationError as exc:
                self.add_error("password1", exc)

        return cleaned_data


class ChangePasswordRequestForm(forms.Form):
    current_password = forms.CharField(
        label="Mật khẩu hiện tại",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Nhập mật khẩu hiện tại",
                "autocomplete": "current-password",
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)

    def clean_current_password(self):
        current_password = self.cleaned_data.get("current_password")
        if not self.user.check_password(current_password):
            raise forms.ValidationError("Mật khẩu hiện tại không đúng.")
        return current_password


class EmailOTPSettingsForm(forms.ModelForm):
    class Meta:
        model = EmailOTPSettings
        fields = [
            "sender_name",
            "sender_email",
            "smtp_host",
            "smtp_port",
            "smtp_username",
            "smtp_password",
            "use_tls",
            "use_ssl",
        ]
        widgets = {
            "sender_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Tên hiển thị"}
            ),
            "sender_email": forms.EmailInput(
                attrs={"class": "form-control", "placeholder": "no-reply@example.com"}
            ),
            "smtp_host": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "smtp.gmail.com"}
            ),
            "smtp_port": forms.NumberInput(
                attrs={"class": "form-control", "placeholder": "587"}
            ),
            "smtp_username": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "SMTP username"}
            ),
            "smtp_password": forms.PasswordInput(
                attrs={"class": "form-control", "placeholder": "SMTP password"},
                render_value=True,
            ),
            "use_tls": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "use_ssl": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        use_tls = cleaned_data.get("use_tls")
        use_ssl = cleaned_data.get("use_ssl")

        if use_tls and use_ssl:
            raise forms.ValidationError("Chỉ nên bật một trong hai chế độ TLS hoặc SSL.")

        return cleaned_data


class SiteBrandSettingsForm(forms.ModelForm):
    class Meta:
        model = SiteBrandSettings
        fields = [
            "logo_image",
            "preloader_image",
            "logo_icon",
            "footer_bottom_text",
        ]
        widgets = {
            "logo_image": forms.ClearableFileInput(
                attrs={"class": "form-control", "accept": "image/*"}
            ),
            "preloader_image": forms.ClearableFileInput(
                attrs={"class": "form-control", "accept": "image/*"}
            ),
            "logo_icon": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ví dụ: fa-solid fa-star hoặc https://fontawesome.com/...",
                }
            ),
            "footer_bottom_text": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "© 2026 Công Ty Xây Dựng Sao Bắc Đẩu | MST: 0123456789",
                }
            ),
        }

    def clean(self):
        cleaned_data = super().clean()
        current_image = getattr(self.instance, "logo_image", None)
        clear_image = bool(self.data.get("logo_image-clear"))
        logo_image = cleaned_data.get("logo_image") or (
            None if clear_image else current_image
        )
        logo_icon = (cleaned_data.get("logo_icon") or "").strip()
        logo_type = getattr(self.instance, "logo_type", SiteBrandSettings.LOGO_TYPE_ICON)
        forced_logo_type = (self.data.get("force_logo_type") or "").strip()

        if forced_logo_type in {
            SiteBrandSettings.LOGO_TYPE_IMAGE,
            SiteBrandSettings.LOGO_TYPE_ICON,
        }:
            logo_type = forced_logo_type
        elif "logo_image" in self.changed_data and cleaned_data.get("logo_image"):
            logo_type = SiteBrandSettings.LOGO_TYPE_IMAGE
        elif "logo_icon" in self.changed_data and logo_icon:
            logo_type = SiteBrandSettings.LOGO_TYPE_ICON
        elif clear_image and logo_icon:
            logo_type = SiteBrandSettings.LOGO_TYPE_ICON

        cleaned_data["logo_type"] = logo_type

        if logo_type == SiteBrandSettings.LOGO_TYPE_IMAGE and not logo_image:
            self.add_error("logo_image", "Vui lòng tải ảnh logo khi chọn kiểu hình ảnh.")

        if logo_type == SiteBrandSettings.LOGO_TYPE_ICON and not logo_icon:
            self.add_error("logo_icon", "Vui lòng nhập class hoặc link icon Font Awesome.")

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.logo_type = self.cleaned_data["logo_type"]

        if instance.logo_type == SiteBrandSettings.LOGO_TYPE_ICON:
            # Khi dùng icon thì bỏ ảnh logo để model cleanup xóa file cũ nếu không còn dùng.
            instance.logo_image = None

        if commit:
            instance.save()
            self.save_m2m()

        return instance
