from django.contrib import admin
from .models import FoodItem, Order, OrderItem

@admin.register(FoodItem)
class FoodItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'is_available', 'created_at')
    list_filter = ('is_available',)
    search_fields = ('name', 'description')

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('item_name', 'unit_price', 'quantity')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id_short', 'customer_name', 'phone', 'fulfilment', 'status', 'payment_method', 'payment_status', 'total', 'created_at')
    list_filter = ('status', 'payment_method', 'payment_status', 'fulfilment', 'created_at')
    search_fields = ('customer_name', 'phone', 'id')
    readonly_fields = ('tracking_token', 'subtotal', 'delivery_fee', 'total', 'created_at', 'updated_at', 'razorpay_order_id', 'razorpay_payment_id')
    inlines = [OrderItemInline]
    def id_short(self, obj): return str(obj.id)[:8]
    id_short.short_description = 'Order'
