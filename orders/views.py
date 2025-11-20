from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages

from .forms import RegisterForm, OrderForm
from .models import Product, Order
from .aws_utils import upload_to_s3, send_order_event_to_sqs
from retail_order_utils import OrderUtils
from .forms import OrderForm, OrderUpdateForm

from django.contrib.auth.decorators import user_passes_test

def is_staff(user):
    return user.is_staff

@user_passes_test(is_staff)
def admin_dashboard_view(request):
    orders = Order.objects.select_related("user", "product").all().order_by("-created_at")
    return render(request, "orders/admin_dashboard.html", {"orders": orders})

def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("product_list")
    else:
        form = RegisterForm()
    return render(request, "registration/register.html", {"form": form})


@login_required
def product_list_view(request):
    products = Product.objects.all()
    return render(request, "orders/product_list.html", {"products": products})


@login_required
def order_list_view(request):
    orders = Order.objects.filter(user=request.user).select_related("product")
    return render(request, "orders/order_list.html", {"orders": orders})


@login_required
def order_create_view(request, product_id=None):
    if request.method == "POST":
        form = OrderForm(request.POST, request.FILES)
        if form.is_valid():
            order_utils = OrderUtils()
            upload_image = form.cleaned_data["upload_image"]

            filename = f"user_uploads/{request.user.id}/{upload_image.name}"
            image_url = upload_to_s3(upload_image, filename)

            estimate = order_utils.create_order_estimate(status="ORDERED")

            order = form.save(commit=False)
            order.user = request.user
            order.order_id = estimate.order_id
            order.status = estimate.status
            order.estimated_delivery = estimate.estimated_delivery
            order.uploaded_image_url = image_url
            order.save()

            send_order_event_to_sqs(order)

            messages.success(request, "Order placed successfully!")
            return redirect("order_list")
    else:
        initial = {}
        if product_id:
            initial["product"] = get_object_or_404(Product, pk=product_id)
        form = OrderForm(initial=initial)

    return render(request, "orders/order_form.html", {"form": form, "title": "Create Order"})


@login_required
def order_update_view(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)

    if not order.can_user_edit():
        messages.error(request, "You can only edit orders in Ordered or Processing state.")
        return redirect("order_detail", pk=order.pk)

    if request.method == "POST":
        form = OrderForm(request.POST, request.FILES, instance=order)
        if form.is_valid():
            upload_image = form.cleaned_data.get("upload_image")
            if upload_image:
                filename = f"user_uploads/{request.user.id}/{upload_image.name}"
                image_url = upload_to_s3(upload_image, filename)
                order.uploaded_image_url = image_url

            order.quantity = form.cleaned_data["quantity"]
            order.product = form.cleaned_data["product"]
            order.save()

            send_order_event_to_sqs(order)
            messages.success(request, "Order updated successfully!")
            return redirect("order_detail", pk=order.pk)
    else:
        class EditOrderForm(OrderForm):
            upload_image = None

        form = EditOrderForm(instance=order)

    return render(request, "orders/order_form.html", {"form": form, "title": "Update Order"})


@login_required
def order_detail_view(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    return render(request, "orders/order_detail.html", {"order": order})


@login_required
def order_delete_view(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)

    if not order.can_user_edit():
        messages.error(request, "You can only delete orders in Ordered or Processing state.")
        return redirect("order_detail", pk=order.pk)

    if request.method == "POST":
        order.delete()
        messages.success(request, "Order deleted.")
        return redirect("order_list")

    return render(request, "orders/order_confirm_delete.html", {"order": order})


def is_staff(user):
    return user.is_staff


@user_passes_test(is_staff)
def admin_order_status_update_view(request, pk):
    order = get_object_or_404(Order, pk=pk)

    if request.method == "POST":
        new_status = request.POST.get("status")
        if new_status not in dict(Order.STATUS_CHOICES):
            messages.error(request, "Invalid status")
        else:
            order_utils = OrderUtils()
            order.status = new_status
            order.estimated_delivery = order_utils.estimate_delivery_by_status(new_status)
            order.save()
            send_order_event_to_sqs(order)
            messages.success(request, "Order status updated")
        return redirect("admin_dashboard")

    return render(
        request,
        "orders/admin_order_status_form.html",
        {"order": order, "status_choices": Order.STATUS_CHOICES},
    )

@login_required
def order_update_view(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)

    if not order.can_user_edit():
        messages.error(request, "You can only edit orders in Ordered or Processing state.")
        return redirect("order_detail", pk=order.pk)

    if request.method == "POST":
        form = OrderUpdateForm(request.POST, request.FILES, instance=order)
        if form.is_valid():
            upload_image = form.cleaned_data.get("upload_image")
            if upload_image:
                filename = f"user_uploads/{request.user.id}/{upload_image.name}"
                image_url = upload_to_s3(upload_image, filename)
                order.uploaded_image_url = image_url

            order.quantity = form.cleaned_data["quantity"]
            order.product = form.cleaned_data["product"]
            order.save()

            send_order_event_to_sqs(order)
            messages.success(request, "Order updated successfully!")
            return redirect("order_detail", pk=order.pk)
    else:
        form = OrderUpdateForm(instance=order)

    return render(request, "orders/order_form.html", {"form": form, "title": "Update Order"})
