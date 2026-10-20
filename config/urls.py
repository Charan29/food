from django.contrib import admin
from django.urls import path
from orders import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.menu, name='menu'),
    path('checkout/', views.checkout, name='checkout'),
    path('order/<uuid:order_id>/', views.order_confirmation, name='order_confirmation'),
    path('track/<str:token>/', views.track_order, name='track_order'),
    path('api/track/<str:token>/', views.track_status_json, name='track_status_json'),
    path('payment/razorpay/<uuid:order_id>/', views.create_razorpay_order, name='create_razorpay_order'),
    path('payment/verify/', views.verify_razorpay_payment, name='verify_razorpay_payment'),
]
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )