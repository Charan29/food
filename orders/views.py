import json
import os
from decimal import Decimal, InvalidOperation
from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST
from .models import FoodItem, Order, OrderItem

DELIVERY_FEE = Decimal(os.getenv('DELIVERY_FEE', '30.00'))

@require_GET
def menu(request):
    items = FoodItem.objects.filter(is_available=True)
    return render(request, 'orders/menu.html', {'items': items, 'razorpay_key_id': os.getenv('RAZORPAY_KEY_ID', '')})

@require_POST
def checkout(request):
    name = request.POST.get('customer_name', '').strip()[:120]
    phone = request.POST.get('phone', '').strip()[:25]
    address = request.POST.get('address', '').strip()[:2000]
    fulfilment = request.POST.get('fulfilment', 'delivery')
    payment_method = request.POST.get('payment_method', 'cash')
    note = request.POST.get('customer_note', '').strip()[:500]
    if not name or not phone or not phone.replace('+', '').replace('-', '').replace(' ', '').isdigit():
        messages.error(request, 'Enter a name and valid phone number.')
        return redirect('menu')
    if fulfilment not in Order.Fulfilment.values or payment_method not in Order.PaymentMethod.values:
        return HttpResponseBadRequest('Invalid fulfilment or payment method.')
    if fulfilment == Order.Fulfilment.DELIVERY and not address:
        messages.error(request, 'Enter a delivery address.')
        return redirect('menu')
    try:
        cart = json.loads(request.POST.get('cart_json', '{}'))
    except (ValueError, TypeError):
        cart = {}
    if not isinstance(cart, dict) or not cart:
        messages.error(request, 'Your cart is empty. Add an item before checkout.')
        return redirect('menu')
    with transaction.atomic():
        order = Order.objects.create(customer_name=name, phone=phone, address=address if fulfilment == 'delivery' else '', fulfilment=fulfilment,
                                     payment_method=payment_method, customer_note=note)
        subtotal = Decimal('0.00')
        for key, raw_qty in cart.items():
            try:
                item_id, qty = int(key), int(raw_qty)
            except (ValueError, TypeError):
                continue
            if qty < 1 or qty > 50:
                continue
            item = FoodItem.objects.filter(pk=item_id, is_available=True).first()
            if not item:
                continue
            OrderItem.objects.create(order=order, food_item=item, item_name=item.name, unit_price=item.price, quantity=qty)
            subtotal += item.price * qty
        if not order.items.exists():
            transaction.set_rollback(True)
            messages.error(request, 'No valid items were found in your cart. Please try again.')
            return redirect('menu')
        order.subtotal = subtotal
        order.delivery_fee = DELIVERY_FEE if fulfilment == 'delivery' else Decimal('0.00')
        order.total = order.subtotal + order.delivery_fee
        order.save(update_fields=['subtotal', 'delivery_fee', 'total', 'updated_at'])
    if payment_method == Order.PaymentMethod.ONLINE:
        return redirect('create_razorpay_order', order_id=order.id)
    return redirect('order_confirmation', order_id=order.id)

@require_GET
def order_confirmation(request, order_id):
    order = get_object_or_404(Order.objects.prefetch_related('items'), id=order_id)
    return render(request, 'orders/confirmation.html', {'order': order})

@require_GET
def track_order(request, token):
    order = get_object_or_404(Order.objects.prefetch_related('items'), tracking_token=token)
    return render(request, 'orders/tracking.html', {'order': order})

@require_GET
def track_status_json(request, token):
    order = get_object_or_404(Order, tracking_token=token)
    return JsonResponse({'status': order.status, 'status_label': order.get_status_display(),
                         'payment_status': order.payment_status, 'payment_label': order.get_payment_status_display(),
                         'updated_at': order.updated_at.isoformat()})

@require_GET
def create_razorpay_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    key_id, key_secret = os.getenv('RAZORPAY_KEY_ID'), os.getenv('RAZORPAY_KEY_SECRET')
    if not key_id or not key_secret:
        messages.error(request, 'Online payments are not configured yet. Configure Razorpay keys or place a cash order.')
        return redirect('order_confirmation', order_id=order.id)
    try:
        import razorpay
        client = razorpay.Client(auth=(key_id, key_secret))
        rp_order = client.order.create({'amount': int(order.total * 100), 'currency': 'INR', 'receipt': str(order.id)[:40], 'notes': {'internal_order_id': str(order.id)}})
        order.razorpay_order_id = rp_order['id']
        order.save(update_fields=['razorpay_order_id', 'updated_at'])
    except Exception:
        messages.error(request, 'Could not start online payment. Please contact the shop or place a cash order.')
        return redirect('order_confirmation', order_id=order.id)
    return render(request, 'orders/pay.html', {'order': order, 'key_id': key_id, 'razorpay_order_id': rp_order['id'], 'public_base_url': os.getenv('PUBLIC_BASE_URL', '').rstrip('/')})

@require_POST
def verify_razorpay_payment(request):
    order_id = request.POST.get('order_id', '')
    payment_id = request.POST.get('razorpay_payment_id', '')
    rp_order_id = request.POST.get('razorpay_order_id', '')
    signature = request.POST.get('razorpay_signature', '')
    order = get_object_or_404(Order, id=order_id, payment_method=Order.PaymentMethod.ONLINE)
    if not order.razorpay_order_id or rp_order_id != order.razorpay_order_id:
        return HttpResponseBadRequest('Payment order mismatch.')
    try:
        import razorpay
        client = razorpay.Client(auth=(os.getenv('RAZORPAY_KEY_ID'), os.getenv('RAZORPAY_KEY_SECRET')))
        client.utility.verify_payment_signature({'razorpay_order_id': rp_order_id, 'razorpay_payment_id': payment_id, 'razorpay_signature': signature})
        # Signature proves checkout response authenticity. For production, also confirm captured status via API/webhook.
        payment = client.payment.fetch(payment_id)
        if payment.get('order_id') != rp_order_id or payment.get('status') not in ('captured', 'authorized'):
            return HttpResponseBadRequest('Payment is not confirmed by the gateway.')
        if payment.get('status') != 'captured':
            client.payment.capture(payment_id, int(order.total * 100))
        order.razorpay_payment_id = payment_id
        order.payment_status = Order.PaymentStatus.PAID
        order.save(update_fields=['razorpay_payment_id', 'payment_status', 'updated_at'])
    except Exception:
        return HttpResponseBadRequest('Payment verification failed. Do not retry repeatedly; contact the shop if money was deducted.')
    return redirect('order_confirmation', order_id=order.id)
