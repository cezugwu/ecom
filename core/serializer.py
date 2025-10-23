from rest_framework import serializers
from .models import Product, Cart, CartItem, Shipping, Country, Ship
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSignUpSerializer(serializers.ModelSerializer):
    password1 = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password1', 'password2']

    def validate(self, attrs):
        if attrs.get("password1") != attrs.get("password2"):
            raise serializers.ValidationError({'error':'password does not match'})
        if User.objects.filter(username=attrs.get("username")).exists():
            raise serializers.ValidationError({'error':'user with username exists'})
        return attrs
    
    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password1"],
        )
        return user
    
class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'title', 'slug', 'image', 'price', 'category', 'description']


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    class Meta:
        model = CartItem
        fields = ['id', 'product', 'quantity']


class CartSerializer(serializers.ModelSerializer):
    total_items = serializers.IntegerField(source="get_total_items", read_only=True)
    total_price = serializers.DecimalField(source="get_total_price", decimal_places=2, max_digits=10, read_only=True)
    link = serializers.CharField(source="get_flutter_link", read_only=True)
    cartitem = CartItemSerializer(read_only=True, many=True) 
    class Meta:
        model = Cart
        fields = ['id', 'cartitem', 'total_items', 'total_price', 'paid', 'link', 'updated_at']


class ShippingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shipping
        fields = '__all__'

class ShippingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shipping
        fields = ['id', 'name', 'phone', 'email', 'city', 'state', 'address', 'zip_code', 'country', 'selected', 'default']

class ShipSerializer(serializers.ModelSerializer):
    shippings = ShippingSerializer(many=True, read_only=True)
    class Meta:
        model = Ship
        fields = ['id', 'shippings']

class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = '__all__'
        