import win32print

from django.utils import timezone


# 🟨 SEWOO 프린터를 자동으로 찾습니다.
def find_sewoo_printer():
    printer_flags = (
        win32print.PRINTER_ENUM_LOCAL
        | win32print.PRINTER_ENUM_CONNECTIONS
    )

    printers = win32print.EnumPrinters(printer_flags)

    for printer in printers:
        printer_name = printer[2]
        upper_name = printer_name.upper()

        if "SLK-TS100" in upper_name or "SEWOO" in upper_name:
            return printer_name

    raise RuntimeError(
        "SEWOO SLK-TS100 프린터를 찾을 수 없습니다."
    )


def encode_text(text):
    # 🟨 한글을 프린터가 읽을 수 있는 CP949 형식으로 변환
    return text.encode("cp949", errors="replace")


def build_order_receipt(order):
    separator = "=" * 42
    short_separator = "-" * 42

    pickup_time = timezone.localtime(order.pickup_at)
    created_time = timezone.localtime(order.created_at)

    receipt = bytearray()

    # 🟨 ESC/POS 프린터 초기화
    receipt.extend(b"\x1b\x40")

    # 가운데 정렬
    receipt.extend(b"\x1b\x61\x01")

    # 굵게 표시
    receipt.extend(b"\x1b\x45\x01")
    receipt.extend(encode_text("픽업 주문\n"))
    receipt.extend(b"\x1b\x45\x00")

    receipt.extend(encode_text(f"{order.store.name}\n"))
    receipt.extend(encode_text(f"{separator}\n"))

    # 왼쪽 정렬
    receipt.extend(b"\x1b\x61\x00")

    receipt.extend(
        encode_text(
            f"출력시간 : "
            f"{created_time:%Y-%m-%d %H:%M}\n"
        )
    )
    receipt.extend(
        encode_text(f"주문번호 : {order.order_number}\n")
    )
    receipt.extend(
        encode_text(
            f"픽업시간 : "
            f"{pickup_time:%Y-%m-%d %H:%M}\n"
        )
    )
    receipt.extend(encode_text(f"{short_separator}\n"))

    # 🟨 주문상품을 DB에서 읽어서 출력
    for item in order.items.select_related("product").all():
        item_total = item.unit_price * item.quantity

        receipt.extend(
            encode_text(
                f"{item.product.name}\n"
                f"  {item.quantity}개 × "
                f"{item.unit_price:,}원"
                f"          {item_total:,}원\n"
            )
        )

    receipt.extend(encode_text(f"{short_separator}\n"))

    # 굵게 표시
    receipt.extend(b"\x1b\x45\x01")
    receipt.extend(
        encode_text(f"합계 : {order.total_price:,}원\n")
    )
    receipt.extend(b"\x1b\x45\x00")

    receipt.extend(
        encode_text(
            f"결제상태 : "
            f"{order.get_payment_status_display()}\n"
        )
    )

    request_message = order.request_message or "없음"
    receipt.extend(
        encode_text(f"요청사항 : {request_message}\n")
    )

    receipt.extend(encode_text(f"{separator}\n"))
    receipt.extend(encode_text("감사합니다.\n\n\n"))

    # 🟨 영수증 자동 절단 명령
    receipt.extend(b"\x1d\x56\x00")

    return bytes(receipt)


def print_order_receipt(order):
    printer_name = find_sewoo_printer()
    receipt_data = build_order_receipt(order)

    printer_handle = win32print.OpenPrinter(printer_name)

    try:
        job_info = (
            "Django 주문 전표",
            None,
            "RAW",
        )

        job_id = win32print.StartDocPrinter(
            printer_handle,
            1,
            job_info,
        )

        try:
            win32print.StartPagePrinter(printer_handle)
            win32print.WritePrinter(
                printer_handle,
                receipt_data,
            )
            win32print.EndPagePrinter(printer_handle)
        finally:
            win32print.EndDocPrinter(printer_handle)

    finally:
        win32print.ClosePrinter(printer_handle)

    # 🟨 정상 출력 후 전표 출력 여부를 DB에 기록
    order.is_printed = True
    order.save(update_fields=["is_printed"])

    return job_id