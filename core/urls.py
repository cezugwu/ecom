from django.urls import path
from . import views

urlpatterns = [
    path('product/', views.products, name='product'),
    path('product/<slug:slug>', views.product, name='productslug'),
    path('cart/', views.cartitem, name='cartitem'),
    path('add/', views.cartadd, name='cartadd'),
    path('remove/', views.cartremove, name='cartremove'),
    path('delete/', views.cartdelete, name='cartdelete'),
    path('clear/', views.cartclear, name='cartclear'),

    path('signup/', views.signup),


    path('shippingid/', views.shippingid, name='shippingid'),
    path('shippingtrue/', views.shippingtrue, name='shippingtrue'),
    path('shippingupdate/', views.shippingupdate, name='shippingupdate'),
    path('shippingcurrent/', views.shippingcurrent, name='shippingcurrent'),
    path('ship/', views.ship, name='ship'),
    path('shipping/', views.shipping, name='shipping'),

    path('flutter/', views.flutter),
    path('fluttercall/', views.fluttercall),
    path('paystack/', views.paystack),
    path('vpaystack/',views.vpaystack),
]

