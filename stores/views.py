from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)

from .forms import ProductForm
from .models import Product, Store


def home(request):
    stores = Store.objects.filter(
        is_active=True,
    ).prefetch_related("products")

    return render(
        request,
        "stores/home.html",
        {"stores": stores},
    )


def product_list(request, store_id):
    store = get_object_or_404(
        Store,
        pk=store_id,
        is_active=True,
    )

    products = store.products.filter(
        is_available=True,
    ).order_by(
        "category",
        "display_order",
        "name",
    )

    context = {
        "store": store,
        "products": products,
    }

    return render(
        request,
        "stores/product_list.html",
        context,
    )


def cart_detail(request, store_id):
    store = get_object_or_404(
        Store,
        pk=store_id,
        is_active=True,
    )

    return render(
        request,
        "stores/cart_detail.html",
        {"store": store},
    )


@login_required
def owner_product_list(request):
    store = Store.objects.filter(
        owner=request.user,
    ).first()

    if store is None:
        return render(
            request,
            "stores/owner_product_list.html",
            {
                "store": None,
                "products": [],
            },
        )

    products = Product.objects.filter(
        store=store,
    ).order_by(
        "display_order",
        "category",
        "name",
    )

    context = {
        "store": store,
        "products": products,
    }

    return render(
        request,
        "stores/owner_product_list.html",
        context,
    )


@login_required
def owner_product_create(request):
    store = Store.objects.filter(
        owner=request.user,
    ).first()

    if store is None:
        messages.error(
            request,
            "현재 계정에 연결된 매장이 없습니다.",
        )

        return redirect(
            "stores:owner_product_list"
        )

    if request.method == "POST":
        form = ProductForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():
            product = form.save(commit=False)
            product.store = store
            product.save()

            messages.success(
                request,
                f"{product.name} 메뉴를 등록했습니다.",
            )

            return redirect(
                "stores:owner_product_list"
            )
    else:
        form = ProductForm()

    context = {
        "form": form,
        "store": store,
        "page_title": "새 메뉴 등록",
        "submit_text": "메뉴 등록",
    }

    return render(
        request,
        "stores/owner_product_form.html",
        context,
    )


@login_required
def owner_product_update(request, product_id):
    # 로그인한 점주의 상품만 수정 가능
    product = get_object_or_404(
        Product,
        pk=product_id,
        store__owner=request.user,
    )

    if request.method == "POST":
        form = ProductForm(
            request.POST,
            request.FILES,
            instance=product,
        )

        if form.is_valid():
            product = form.save()

            messages.success(
                request,
                f"{product.name} 메뉴를 수정했습니다.",
            )

            return redirect(
                "stores:owner_product_list"
            )
    else:
        form = ProductForm(
            instance=product,
        )

    context = {
        "form": form,
        "store": product.store,
        "product": product,
        "page_title": "메뉴 수정",
        "submit_text": "변경사항 저장",
    }

    return render(
        request,
        "stores/owner_product_form.html",
        context,
    )

def cart_detail(request, store_id):
    store = get_object_or_404(
        Store,
        pk=store_id,
        is_active=True,
    )

    return render(
        request,
        "stores/cart_detail.html",
        {"store": store},
    )