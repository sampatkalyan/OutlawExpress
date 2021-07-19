from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import auth, messages
from .models import Order, OrderProduct, Payment
from .forms import OrderForm
from carts.models import CartItem
from store.models import Product
import datetime
import json
# Mail Imports
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

# Create your views here.


def payments(request):
    body = json.loads(request.body)
    order = Order.objects.get(
        user=request.user, is_ordered=False, order_number=body['orderid'])
    # Store all transaction detials inside payment model
    payment = Payment()
    payment.user = request.user
    payment.payment_id = body['transID']
    payment.payement_method = body['payment_method']
    payment.amount_paid = order.order_total
    payment.status = body['status']
    payment.save()
    order.payment = payment
    order.is_ordered = True
    order.save()

    # move cart items to order items
    cart_items = CartItem.objects.filter(user=request.user)
    for item in cart_items:
        order_product = OrderProduct()
        order_product.order_id = order.id
        order_product.payment = payment
        order_product.user_id = request.user.id
        order_product.product_id = item.product_id
        order_product.quantity = item.quantity
        order_product.product_price = item.product.price
        order_product.ordered = True
        order_product.save()

        cart_item = CartItem.objects.get(id=item.id)
        product_variations = cart_item.variations.all()
        order_product = OrderProduct.objects.get(id=order_product.id)
        order_product.variation.set(product_variations)
        order_product.save()
        # reduce the quantity of sold products
        product = Product.objects.get(id=item.product_id)
        product.stock -= item.quantity
        product.save()

    # Clear cart
    CartItem.objects.filter(user=request.user).delete()
    # SEND  ORDER Number and transication Id back to senddata method via json method
    mail_subject = 'Thank you for your Order'
    message = render_to_string('orders/order_recived_email.html', {
        'user': request.user,
        'order': order,
        'payment': payment
    })
    mail = request.user.email
    send_mail = EmailMessage(mail_subject, message, to=[mail])
    send_mail.send()

    data = {
        'order_number': order.order_number,
        'payment': payment.payment_id,

    }
    return JsonResponse(data)


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
        return redirect('store')
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
            data.save()
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


def order_complete(request):
    order_number = request.GET.get('order_number')
    payment_id = request.GET.get('payment_id')
    try:
        order = Order.objects.get(order_number=order_number, is_ordered=True)
        order_products = OrderProduct.objects.filter(order_id=order.id)
        payment = Payment.objects.get(payment_id=payment_id)

        sub_total = 0
        for i in order_products:
            sub_total += i.quantity*i.product_price
        context = {
            'order': order,
            'order_products': order_products,
            'payment_id': payment.payment_id,
            'payment': payment,
            'sub_total': sub_total
        }
        return render(request, 'orders/order_complete.html', context)
    except(Payment.DoesNotExist, Order.DoesNotExist):
        return redirect('home')
