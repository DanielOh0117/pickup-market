import re

from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import EmailOTP, User


def normalize_phone(value):
    # 010-1234-5678, 010 1234 5678 → 01012345678 (숫자만 저장)
    digits = re.sub(r"\D", "", value or "")

    if not re.fullmatch(r"01\d{8,9}", digits):
        raise forms.ValidationError(
            "휴대전화 번호 형식이 올바르지 않습니다. "
            "예: 01012345678"
        )

    return digits


class UserAddForm(forms.ModelForm):
    password1 = forms.CharField(
        label="비밀번호",
        required=False,
        strip=False,
        widget=forms.PasswordInput,
        help_text=(
            "관리자 계정만 입력하세요. 고객·점주는 비워 두면 "
            "인증번호 로그인용 계정으로 만들어집니다."
        ),
    )
    password2 = forms.CharField(
        label="비밀번호 확인",
        required=False,
        strip=False,
        widget=forms.PasswordInput,
    )

    class Meta:
        model = User
        fields = ("phone_number", "email", "role")

    def clean_phone_number(self):
        return normalize_phone(
            self.cleaned_data["phone_number"]
        )

    def clean(self):
        cleaned = super().clean()

        pw1 = cleaned.get("password1")
        pw2 = cleaned.get("password2")

        if pw1 != pw2:
            self.add_error(
                "password2",
                "비밀번호가 서로 다릅니다.",
            )

        if cleaned.get("role") == "admin" and not pw1:
            self.add_error(
                "password1",
                "관리자 계정은 비밀번호가 필요합니다.",
            )

        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get("password1")

        if password:
            user.set_password(password)
        else:
            # 고객·점주는 고정 비밀번호를 쓰지 않음
            user.set_unusable_password()

        # 관리자 유형은 관리자 화면 로그인 가능
        if user.role == "admin":
            user.is_staff = True

        if commit:
            user.save()
            self.save_m2m()

        return user


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    add_form = UserAddForm

    list_display = (
        "phone_number",
        "email",
        "role",
        "is_active",
        "date_joined",
    )
    list_filter = ("role", "is_active", "is_staff")
    search_fields = ("phone_number", "email")
    ordering = ("-date_joined",)

    fieldsets = (
        (None, {"fields": ("phone_number", "password")}),
        ("기본 정보", {
            "fields": ("first_name", "last_name", "email"),
        }),
        ("회원 유형·권한", {
            "fields": (
                "role",
                "is_active",
                "is_staff",
                "is_superuser",
                "groups",
                "user_permissions",
            ),
        }),
        ("기록", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "phone_number",
                "email",
                "role",
                "password1",
                "password2",
            ),
        }),
    )


@admin.register(EmailOTP)
class EmailOTPAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "is_used",
        "failed_attempts",
        "expires_at",
        "created_at",
    )
    list_filter = ("is_used",)
    search_fields = ("user__phone_number", "user__email")
    readonly_fields = (
        "user",
        "code_hash",
        "expires_at",
        "is_used",
        "failed_attempts",
        "created_at",
    )

    def has_add_permission(self, request):
        return False