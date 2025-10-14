from rest_framework import serializers
from .models import Product, Cart, CartItem, Shipping, Country
from django.contrib.auth.models import User


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'slug', 'image', 'price', 'category', 'description']


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    price_total = serializers.SerializerMethodField()
    class Meta:
        model = CartItem
        fields = ['id', 'quantity', 'product', 'price_total']

    def get_price_total(self, obj):
        total = obj.quantity * obj.product.price
        return total
    
class NewCartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    order_id = serializers.SerializerMethodField()
    order_date = serializers.SerializerMethodField()
    class Meta:
        model = CartItem
        fields = ['id', 'quantity', 'product', 'order_id', 'order_date']

    def get_order_id(self, obj):
        order_id = obj.cart.cart_code
        return order_id
    
    def get_order_date(self, obj):
        order_date = obj.cart.modified_at
        return order_date


class CartSerializer(serializers.ModelSerializer):
    cartitem = CartItemSerializer(read_only=True, many=True)
    total_item = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()
    class Meta:
        model = Cart
        fields = ['id', 'cartitem', 'total_item', 'total_price']

    def get_total_item(self, obj):
        cartitem = obj.cartitem.all()
        total = sum([item.quantity for item in cartitem])
        return total
    
    def get_total_price(self, obj):
        cartitem = obj.cartitem.all()
        total = sum([(item.quantity * item.product.price) for item in cartitem])
        return total

class UserSerializer(serializers.ModelSerializer):
    item = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'item']

    def get_item(self, user):
        cartitem = CartItem.objects.filter(cart__user=user, cart__paid=True)
        serializer = NewCartItemSerializer(cartitem, many=True)
        return serializer.data
    
class ShippingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shipping
        fields = '__all__'

class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = '__all__'
        