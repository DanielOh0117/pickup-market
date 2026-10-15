from decimal import Decimal, ROUND_CEILING

from django.db import models
from django.conf import settings


class Store(models.Model):
    # 🟨 이 매장을 관리하는 점주
    # 기존 매장이 있으므로 우선 null=True, blank=True로 추가
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="owned_stores",
        verbose_name="점주",
        null=True,
        blank=True,
    )

    name = models.CharField(
        "매장명",
        max_length=100,
    )

    address = models.CharField(
        "주소",
        max_length=200,
    )

    phone = models.CharField(
        "전화번호",
        max_length=20,
        blank=True,
    )

    is_active = models.BooleanField(
        "운영 여부",
        default=True,
    )

    created_at = models.DateTimeField(
        "등록일",
        auto_now_add=True,
    )

    def __str__(self):
        return self.name


class Product(models.Model):
    CATEGORY_CHOICES = [
        ("coffee", "커피 원두·로스팅"),
        ("drink", "카페 음료"),
        ("fruit", "과일"),
        ("food", "음식 메뉴"),
    ]

    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name="products",
        verbose_name="매장",
    )

    category = models.CharField(
        "상품 분류",
        max_length=20,
        choices=CATEGORY_CHOICES,
    )

    name = models.CharField(
        "상품명",
        max_length=100,
    )

    description = models.TextField(
        "상품 설명",
        blank=True,
    )

    # 🟨 휴대폰에서 촬영하거나 선택한 메뉴 대표사진
    image = models.ImageField(
        "대표사진",
        upload_to="products/%Y/%m/",
        blank=True,
        null=True,
    )

    price = models.PositiveIntegerField(
        "가격",
    )

    preparation_minutes = models.PositiveIntegerField(
        "준비시간(분)",
        default=10,
    )

    # False이면 고객 메뉴목록에서 숨김
    is_available = models.BooleanField(
        "판매 여부",
        default=True,
    )

    # True이면 메뉴는 보이지만 주문할 수 없음
    is_sold_out = models.BooleanField(
        "품절 여부",
        default=False,
    )

    # 숫자가 낮은 메뉴를 먼저 표시
    display_order = models.PositiveIntegerField(
        "노출 순서",
        default=0,
    )

    created_at = models.DateTimeField(
        "등록일",
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        "수정일",
        auto_now=True,
    )

    def _pricing_ready(self):
        return bool(
            self.wholesale_price is not None
            and self.wholesale_amount
            and self.margin_percent is not None
        )

    @staticmethod
    def _round_up_10(value):
        return int(
            (value / 10).to_integral_value(
                rounding=ROUND_CEILING
            ) * 10
        )

    @property
    def unit_cost(self):
        """도매 기준 단위당 원가 (점주용)"""
        if not self._pricing_ready():
            return None

        return (
            Decimal(self.wholesale_price)
            / Decimal(self.wholesale_amount)
            * self.unit_base
        )

    @property
    def unit_sale_price(self):
        """고객에게 보이는 기준 단위당 소비자가"""
        cost = self.unit_cost

        if cost is None:
            return None

        raw = cost * (
            1 + Decimal(self.margin_percent) / 100
        )
        return self._round_up_10(raw)

    def save(self, *args, **kwargs):
        # 가격 계산 정보가 모두 있으면 판매가를 자동 산출
        if self._pricing_ready() and self.sale_amount:
            raw = (
                self.unit_sale_price
                * Decimal(self.sale_amount)
                / self.unit_base
            )
            self.price = self._round_up_10(raw)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    UNIT_CHOICES = [
        ("g", "g"),
        ("ml", "ml"),
        ("ea", "개"),
    ]

    # 🟨 점주 전용: 고객 화면에는 절대 표시하지 않음
    wholesale_price = models.PositiveIntegerField(
        "도매가격(원)",
        null=True,
        blank=True,
    )

    wholesale_amount = models.DecimalField(
        "도매 총 용량",
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )

    unit_type = models.CharField(
        "용량 단위",
        max_length=5,
        choices=UNIT_CHOICES,
        default="g",
    )

    unit_base = models.PositiveIntegerField(
        "기준 단위",
        default=100,
    )

    margin_percent = models.DecimalField(
        "마진율(%)",
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
    )

    sale_amount = models.DecimalField(
        "판매 용량",
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )

class Order(models.Model):
    ORDER_TYPE_CHOICES = [
        ("pickup", "픽업 주문"),
        ("visit", "방문 예약"),
    ]

    STATUS_CHOICES = [
        ("pending", "접수 대기"),
        ("accepted", "주문 접수"),
        ("preparing", "준비 중"),
        ("ready", "픽업 가능"),
        ("completed", "완료"),
        ("cancelled", "취소"),
    ]

    PAYMENT_STATUS_CHOICES = [
        ("pending", "결제 대기"),
        ("paid", "결제 완료"),
        ("cancelled", "결제 취소"),
        ("refunded", "환불 완료"),
    ]

    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name="orders",
        verbose_name="매장",
    )

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
        verbose_name="고객",
    )

    order_type = models.CharField(
        "이용 유형",
        max_length=20,
        choices=ORDER_TYPE_CHOICES,
        default="pickup",
    )

    order_number = models.CharField(
        "주문번호",
        max_length=30,
        unique=True,
    )

    pickup_at = models.DateTimeField(
        "방문·픽업 예정시간",
    )

    status = models.CharField(
        "주문 상태",
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
    )

    payment_status = models.CharField(
        "결제 상태",
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default="pending",
    )

    request_message = models.TextField(
        "요청사항",
        blank=True,
    )

    total_price = models.PositiveIntegerField(
        "총 결제금액",
        default=0,
    )

    is_printed = models.BooleanField(
        "전표 출력 여부",
        default=False,
    )

    # 점주가 주문 접수 후 확정하는 예상 준비완료시간
    estimated_ready_at = models.DateTimeField(
        "예상 준비완료시간",
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        "주문일시",
        auto_now_add=True,
    )

    def __str__(self):
        return self.order_number


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="주문",
    )

    # PROTECT이므로 주문기록에 사용된 상품은 함부로 삭제되지 않음
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="order_items",
        verbose_name="상품",
    )

    quantity = models.PositiveIntegerField(
        "수량",
        default=1,
    )

    # 상품 가격이 바뀌어도 주문 당시 가격 보존
    unit_price = models.PositiveIntegerField(
        "주문 당시 단가",
    )

    @property
    def subtotal(self):
        return self.unit_price * self.quantity

    def __str__(self):
        return f"{self.product.name} × {self.quantity}"