from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Product(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image_url = models.URLField(blank=True)

    def __str__(self) -> str:
        return self.name


class Order(models.Model):
    STATUS_CHOICES = [
        ("ORDERED", "ORDERED"),
        ("PROCESSING", "PROCESSING"),
        ("TRANSIT", "TRANSIT"),
        ("READY_FOR_DELIVERY", "READY FOR DELIVERY"),
        ("DELIVERED", "DELIVERED"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="orders")
    quantity = models.PositiveIntegerField(default=1)

    order_id = models.CharField(max_length=40, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="ORDERED")

    uploaded_image_url = models.URLField()
    estimated_delivery = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def can_user_edit(self) -> bool:
        return self.status in ("ORDERED", "PROCESSING")

    def __str__(self) -> str:
        return f"{self.order_id} - {self.product.name}"
