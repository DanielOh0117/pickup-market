from django import forms
from django.core.exceptions import ValidationError

from .models import Product


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product

        fields = (
            "category",
            "name",
            "description",
            "image",
            "wholesale_price",
            "wholesale_amount",
            "unit_type",
            "unit_base",
            "margin_percent",
            "sale_amount",
            "price",
            "preparation_minutes",
            "is_available",
            "is_sold_out",
            "display_order",
        )

        widgets = {
            "category": forms.Select(
                attrs={"class": "form-control"}
            ),
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "예: 아이스 아메리카노",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": "메뉴의 특징과 구성 등을 입력하세요.",
                }
            ),
            "image": forms.ClearableFileInput(
                attrs={
                    "class": "form-control",
                    "accept": "image/*",
                }
            ),
            # 🟨 가격 자동계산 입력 (점주 전용)
            "wholesale_price": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 0,
                    "inputmode": "numeric",
                    "placeholder": "예: 25000",
                }
            ),
            "wholesale_amount": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 0,
                    "step": "any",
                    "inputmode": "decimal",
                    "placeholder": "예: 1000",
                }
            ),
            "unit_type": forms.Select(
                attrs={"class": "form-control"}
            ),
            "unit_base": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 1,
                    "inputmode": "numeric",
                }
            ),
            "margin_percent": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 0,
                    "step": "any",
                    "inputmode": "decimal",
                    "placeholder": "예: 30",
                }
            ),
            "sale_amount": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 0,
                    "step": "any",
                    "inputmode": "decimal",
                    "placeholder": "예: 200",
                }
            ),
            "price": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 0,
                    "inputmode": "numeric",
                }
            ),
            "preparation_minutes": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 1,
                    "inputmode": "numeric",
                }
            ),
            "is_available": forms.CheckboxInput(
                attrs={"class": "form-checkbox"}
            ),
            "is_sold_out": forms.CheckboxInput(
                attrs={"class": "form-checkbox"}
            ),
            "display_order": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 0,
                    "inputmode": "numeric",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 🟨 가격 자동계산을 쓰면 판매가격은 비워도 됨
        self.fields["price"].required = False
        self.fields["price"].help_text = (
            "자동계산 항목을 모두 입력하면 판매가격은 "
            "저장할 때 자동으로 정해집니다."
        )

    def clean(self):
        cleaned = super().clean()

        pricing_values = [
            cleaned.get("wholesale_price"),
            cleaned.get("wholesale_amount"),
            cleaned.get("margin_percent"),
            cleaned.get("sale_amount"),
        ]

        filled = [v is not None for v in pricing_values]

        if any(filled) and not all(filled):
            raise ValidationError(
                "가격 자동계산을 사용하려면 도매가격, 도매 총 용량, "
                "마진율, 판매 용량을 모두 입력해 주세요."
            )

        if all(filled):
            if cleaned["wholesale_amount"] <= 0:
                self.add_error(
                    "wholesale_amount",
                    "도매 총 용량은 0보다 커야 합니다.",
                )

            if cleaned["sale_amount"] <= 0:
                self.add_error(
                    "sale_amount",
                    "판매 용량은 0보다 커야 합니다.",
                )

        if (
            not any(filled)
            and cleaned.get("price") is None
            and "price" not in self.errors
        ):
            self.add_error(
                "price",
                "판매가격을 입력하거나, 가격 자동계산 항목을 "
                "모두 입력해 주세요.",
            )

        return cleaned