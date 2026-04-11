from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

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
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "Email (không bắt buộc)",
                "autocomplete": "email",
            }
        ),
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "password1", "password2")

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
            {"class": "form-control", "placeholder": "Mật khẩu", "autocomplete": "new-password"}
        )
        self.fields["password2"].widget.attrs.update(
            {
                "class": "form-control",
                "placeholder": "Nhập lại mật khẩu",
                "autocomplete": "new-password",
            }
        )
