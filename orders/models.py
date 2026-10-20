import secrets
import uuid
from decimal import Decimal
from django.conf import settings
from django.db import models
from django.utils import timezone

def generate_tracking_token():
    return secrets.token_urlsafe(32)

class FoodItem(models.Model):
    name = models.CharField(max_length=120)
    description = models.CharField(max_length=300, blank=True)
    price = models.DecimalField(max_digits=9, decimal_places=2)
    image_url = models.URLField(blank=True)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
    def __str__(self):
        return f'{self.name} (₹{self.price})'

class Order(models.Model):
    class Status(models.TextChoices):
        RECEIVED = 'received', 'Order received'
        CONFIRMED = 'confirmed', 'Confirmed'
        PREPARING = 'preparing', 'Preparing'
        READY = 'ready', 'Ready for pickup / dispatch'
        OUT = 'out_for_delivery', 'Out for delivery'
        DELIVERED = 'delivered', 'Delivered / picked up'
        CANCELLED = 'cancelled', 'Cancelled'
    class PaymentMethod(models.TextChoices):
        CASH = 'cash', 'Cash on delivery / pickup'
        ONLINE = 'online', 'Online payment'
    class PaymentStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PAID = 'paid', 'Paid'
        FAILED = 'failed', 'Failed'
        REFUNDED = 'refunded', 'Refunded'
    class Fulfilment(models.TextChoices):
        DELIVERY = 'delivery', 'Delivery'
        PICKUP = 'pickup', 'Pickup'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tracking_token = models.CharField(max_length=64, unique=True, default=generate_tracking_token, editable=False)
    customer_name = models.CharField(max_length=120)
    phone = models.CharField(max_length=25)
    address = models.TextField(blank=True)
    fulfilment = models.CharField(max_length=12, choices=Fulfilment.choices, default=Fulfilment.DELIVERY)
    payment_method = models.CharField(max_length=10, choices=PaymentMethod.choices)
    payment_status = models.CharField(max_length=10, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.RECEIVED)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    delivery_fee = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    customer_note = models.CharField(max_length=500, blank=True)
    razorpay_order_id = models.CharField(max_length=100, blank=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ['-created_at']
    def __str__(self):
        return f'Order {str(self.id)[:8]} — {self.customer_name}'

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    food_item = models.ForeignKey(FoodItem, null=True, on_delete=models.SET_NULL)
    item_name = models.CharField(max_length=120)
    unit_price = models.DecimalField(max_digits=9, decimal_places=2)
    quantity = models.PositiveIntegerField()
    @property
    def line_total(self):
        return self.unit_price * self.quantity
    def __str__(self):
        return f'{self.quantity} × {self.item_name}'
        
