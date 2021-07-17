from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import auth, messages
from .models import Order, OrderProduct, Payment
from .forms import OrderForm
from carts.models import CartItem
import datetime
# Create your views here.


def payments(request):
    return render(request, 'orders/payments.html')


def place_order(request, quantity=0, total=0):
    current_user = request.user
    cart_items = CartItem.objects.filter(user=current_user)
    cart_count = cart_items.count()
    tax = 0
    grand_total = 0
    for cart_item in cart_items:
        quantity += cart_item.quantity
        total += cart_item.quantity*cart_item.product.price
    tax = (5*total)/100
    grand_total = tax+total
    if cart_count <= 0:
        return redirect()
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            data = Order()
            data.first_name = form.cleaned_data['first_name']
            data.last_name = form.cleaned_data['last_name']
            data.phone = form.cleaned_data['phone']
            data.email = form.cleaned_data['email']
            data.address_line_1 = form.cleaned_data['address_line_1']
            data.address_line_2 = form.cleaned_data['address_line_2']
            data.city = form.cleaned_data['city']
            data.state = form.cleaned_data['state']
            data.pincode = form.cleaned_data['pincode']
            data.order_note = form.cleaned_data['order_note']
            data.order_total = grand_total
            data.tax = tax
            data.ip = request.META.get('REMOTE_ADDR')
            data.user = current_user
            print(data)
            data.save()
            print(data)
            # generate order number
            yr = int(datetime.date.today().strftime('%Y'))
            mt = int(datetime.date.today().strftime('%m'))
            dt = int(datetime.date.today().strftime('%d'))
            d = datetime.date(yr, mt, dt)
            current_date = d.strftime('%Y%m%d')
            order_number = current_date+str(data.id)
            data.order_number = order_number
            data.save()

            order = Order.objects.get(user=current_user,
                                      is_ordered=False, order_number=order_number)
            context = {
                'order': order,
                'cart_items': cart_items,
                'total': total,
                'tax': tax,
                'grand_total': grand_total,
            }

            return render(request, 'orders/payments.html', context)
        else:
            return redirect('checkout')
