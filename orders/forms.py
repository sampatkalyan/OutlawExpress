from django import forms
from .models import Order


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['first_name', 'last_name', 'email', 'phone', 'address_line_1',
                  'address_line_2', 'city', 'state', 'pincode', 'order_note']
