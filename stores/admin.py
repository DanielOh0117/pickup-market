from django.contrib import admin, messages
from django.shortcuts import redirect
from django.urls import path, reverse
from django.utils.html import format_html

from .models import Order, OrderItem, Product, Store
from .printer import print_order_receipt


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "owner",
        "address",
        "phone",
        "is_active",
        "created_at",
    )

    list_filter = (
        "is_active",
    )

    search_fields = (
        "name",
        "address",
        "phone",
        "owner__phone_number",
        "owner__email",
    )


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "image_preview",
        "name",
        "store",
        "category",
        "price",
        "preparation_minutes",
        "is_available",
        "is_sold_out",
        "display_order",
        "updated_at",
    )

    list_filter = (
        "store",
        "category",
        "is_available",
        "is_sold_out",
    )

    search_fields = (
        "name",
        "description",
        "store__name",
    )

    # 상품목록에서 바로 수정할 수 있는 항목
    list_editable = (
        "price",
        "preparation_minutes",
        "is_available",
        "is_sold_out",
        "display_order",
    )

    readonly_fields = (
        "image_preview_large",
        "created_at",
        "updated_at",
    )

    ordering = (
        "store",
        "display_order",
        "name",
    )

    @admin.display(description="사진")
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" '
                'style="width:50px; height:50px; '
                'object-fit:cover; border-radius:6px;">',
                obj.image.url,
            )

        return "사진 없음"

    @admin.display(description="현재 사진")
    def image_preview_large(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" '
                'style="max-width:300px; max-height:300px; '
                'object-fit:contain; border-radius:10px;">',
                obj.image.url,
            )

        return "등록된 사진이 없습니다."


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

    fields = (
        "product",
        "quantity",
        "unit_price",
        "item_subtotal",
    )

    readonly_fields = (
        "item_subtotal",
    )

    @admin.display(description="상품 합계")
    def item_subtotal(self, obj):
        if obj.pk:
            return f"{obj.subtotal:,}원"

        return "-"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    actions = (
        "print_selected_orders",
    )

    list_display = (
        "order_number",
        "print_button",
        "store",
        "order_type",
        "pickup_at",
        "estimated_ready_at",
        "status",
        "payment_status",
        "formatted_total_price",
        "is_printed",
        "created_at",
    )

    list_filter = (
        "store",
        "order_type",
        "status",
        "payment_status",
        "is_printed",
        "pickup_at",
    )

    search_fields = (
        "order_number",
        "store__name",
        "customer__phone_number",
        "request_message",
    )

    readonly_fields = (
        "created_at",
        "formatted_total_price",
    )

    date_hierarchy = "pickup_at"

    inlines = (
        OrderItemInline,
    )

    # 개별 주문 출력 주소 추가
    def get_urls(self):
        default_urls = super().get_urls()

        custom_urls = [
            path(
                "<path:object_id>/print-receipt/",
                self.admin_site.admin_view(
                    self.print_receipt_view
                ),
                name="stores_order_print_receipt",
            ),
        ]

        return custom_urls + default_urls

    # 주문번호 오른쪽에 출력 버튼 생성
    @admin.display(description="전표 출력")
    def print_button(self, obj):
        print_url = reverse(
            "admin:stores_order_print_receipt",
            args=[obj.pk],
        )

        return format_html(
            '<a class="button" href="{}">'
            "🖨️ 출력"
            "</a>",
            print_url,
        )

    # 출력 버튼을 눌렀을 때 실행
    def print_receipt_view(self, request, object_id):
        order = self.get_object(request, object_id)

        if order is None:
            self.message_user(
                request,
                "주문을 찾을 수 없습니다.",
                level=messages.ERROR,
            )

            return redirect(
                "admin:stores_order_changelist"
            )

        try:
            print_order_receipt(order)

            self.message_user(
                request,
                f"{order.order_number} 전표를 출력했습니다.",
                level=messages.SUCCESS,
            )

        except Exception as error:
            self.message_user(
                request,
                f"출력 실패: {error}",
                level=messages.ERROR,
            )

        return redirect(
            "admin:stores_order_changelist"
        )

    @admin.display(description="총 결제금액")
    def formatted_total_price(self, obj):
        return f"{obj.total_price:,}원"

    # 여러 주문을 한꺼번에 출력
    @admin.action(
        description="선택한 주문을 SEWOO 전표로 출력"
    )
    def print_selected_orders(self, request, queryset):
        success_count = 0
        failed_orders = []

        for order in queryset.prefetch_related(
            "items__product"
        ):
            try:
                print_order_receipt(order)
                success_count += 1

            except Exception as error:
                failed_orders.append(
                    f"{order.order_number}: {error}"
                )

        if success_count:
            self.message_user(
                request,
                f"{success_count}건의 주문 전표를 출력했습니다.",
                level=messages.SUCCESS,
            )

        if failed_orders:
            self.message_user(
                request,
                "출력 실패 - " + " / ".join(failed_orders),
                level=messages.ERROR,
            )


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        "order",
        "product",
        "quantity",
        "unit_price",
        "formatted_subtotal",
    )

    search_fields = (
        "order__order_number",
        "product__name",
    )

    @admin.display(description="상품 합계")
    def formatted_subtotal(self, obj):
        return f"{obj.subtotal:,}원"