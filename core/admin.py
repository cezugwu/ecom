from django.contrib import admin
from .models import Product, Cart, CartItem, TransactionFlutter, TransactionPaystack, Shipping, Country

admin.site.register(Product)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(TransactionFlutter)
admin.site.register(TransactionPaystack)
admin.site.register(Shipping)
admin.site.register(Country)
