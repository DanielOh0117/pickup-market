from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(
        self,
        phone_number,
        email,
        password=None,
        **extra_fields,
    ):
        if not phone_number:
            raise ValueError("휴대전화 번호는 필수입니다.")

        if not email:
            raise ValueError("이메일 주소는 필수입니다.")

        email = self.normalize_email(email)

        user = self.model(
            phone_number=phone_number,
            email=email,
            **extra_fields,
        )

        if password:
            user.set_password(password)
        else:
            # 🟨 일반 고객과 점주는 고정 비밀번호를 사용하지 않음
            user.set_unusable_password()

        user.save(using=self._db)
        return user

    def create_superuser(
        self,
        phone_number,
        email,
        password=None,
        **extra_fields,
    ):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("role", "admin")

        if extra_fields.get("is_staff") is not True:
            raise ValueError("최고관리자는 is_staff=True여야 합니다.")

        if extra_fields.get("is_superuser") is not True:
            raise ValueError("최고관리자는 is_superuser=True여야 합니다.")

        if not password:
            raise ValueError("최고관리자 비밀번호는 필수입니다.")

        return self.create_user(
            phone_number,
            email,
            password,
            **extra_fields,
        )


class User(AbstractUser):
    ROLE_CHOICES = [
        ("customer", "고객"),
        ("owner", "점주"),
        ("admin", "관리자"),
    ]

    username = None  # 🟨 기존 아이디 필드 제거

    phone_number = models.CharField(
        "휴대전화 번호",
        max_length=20,
        unique=True,  # 🟨 전화번호를 중복 없는 로그인 아이디로 사용
    )
    email = models.EmailField(
        "이메일 주소",
        unique=True,  # 🟨 인증번호를 받을 필수 이메일
    )
    role = models.CharField(
        "회원 유형",
        max_length=20,
        choices=ROLE_CHOICES,
        default="customer",  # 🟨 고객·점주·관리자 구분
    )

    USERNAME_FIELD = "phone_number"  # 🟨 로그인 아이디 지정
    REQUIRED_FIELDS = ["email"]

    objects = UserManager()

    def __str__(self):
        return f"{self.phone_number} ({self.get_role_display()})"


class EmailOTP(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="email_otps",
        verbose_name="사용자",
    )
    code_hash = models.CharField(
        "인증번호 해시",
        max_length=128,  # 🟨 인증번호 원문을 저장하지 않음
    )
    expires_at = models.DateTimeField("만료시간")
    is_used = models.BooleanField("사용 여부", default=False)
    failed_attempts = models.PositiveSmallIntegerField(
        "입력 실패 횟수",
        default=0,
    )
    created_at = models.DateTimeField("생성일", auto_now_add=True)

    def set_code(self, raw_code):
        # 🟨 6자리 인증번호를 암호화하여 저장
        self.code_hash = make_password(raw_code)

    def verify_code(self, raw_code):
        if self.is_used:
            return False

        if timezone.now() >= self.expires_at:
            return False

        if self.failed_attempts >= 5:
            return False

        if check_password(raw_code, self.code_hash):
            self.is_used = True
            self.save(update_fields=["is_used"])
            return True

        self.failed_attempts += 1
        self.save(update_fields=["failed_attempts"])
        return False

    def __str__(self):
        return f"{self.user.phone_number} - {self.created_at}"