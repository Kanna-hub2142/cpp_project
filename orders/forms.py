from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from .models import Order

User = get_user_model()


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")


class OrderForm(forms.ModelForm):
    """
    Form used by users when creating or updating an order.
    Image is uploaded to S3 in the view, so here we accept FileField.
    """
    upload_image = forms.ImageField(required=True)

    class Meta:
        model = Order
        fields = ["product", "quantity", "upload_image"]

class OrderUpdateForm(forms.ModelForm):
    upload_image = forms.ImageField(required=False)

    class Meta:
        model = Order
        fields = ["product", "quantity"]
