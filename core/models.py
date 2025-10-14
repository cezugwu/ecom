from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
import secrets
import string
from cloudinary.models import CloudinaryField

def generate_cart_code(length=10):
    characters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))

    
class Product(models.Model):
    CATEGORY_CHOICES = (
        ('ELECTRONICS', 'Electronics'),
        ('JEWELRY', 'Jewelry'),
        ('CLOTHINGS', 'Clothings'),
    )

    name = models.CharField(max_length=255, null=True, blank=True)
    slug = models.SlugField(unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = CloudinaryField('image_ecommerce', blank=True, null=True)
    category = models.CharField(max_length=255, null=True, blank=True, choices=CATEGORY_CHOICES)
    description = models.TextField()

    def __str__(self):
        return self.name

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    cart_code = models.CharField(max_length=255, unique=True, null=True, blank=True)
    paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    
    def save(self, *args, **kwargs):
        if not self.cart_code: 
            self.cart_code = generate_cart_code()
        super().save(*args, **kwargs)

    def __str__(self):
        if self.user:
            return f'{self.user.username} - {self.cart_code or ''} - {self.paid}'
        return self.cart_code or ''

    
class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='cartitem')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=0)

    def __str__(self):
        return f'{self.quantity} quantity of {self.product.name} in cart {self.cart.id}'
    

class Shipping(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shipping')
    city = models.CharField(max_length=255, null=True, blank=True)
    state = models.CharField(max_length=255, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    zip_code = models.CharField(max_length=20, blank=True, null=True)
    phone = models.CharField(max_length=255, null=True, blank=True)
    contact_name = models.CharField(max_length=255, null=True, blank=True)
    country = models.CharField(max_length=255, null=True, blank=True)
    phone_code = models.CharField(max_length=255, null=True, blank=True)

class TransactionFlutter(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='transactionflutter')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    tx_ref = models.CharField(max_length=255, unique=True)
    transaction_id = models.CharField(max_length=255, null=True, blank=True)
    currency = models.CharField(max_length=20, default='NGN')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.status} - {self.user.username} - {self.cart.cart_code}'

class TransactionPaystack(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='transactionpaystack')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    reference = models.CharField(max_length=255, null=True, blank=True)
    access_code = models.CharField(max_length=255, null=True, blank=True)
    transaction_id = models.CharField(max_length=255, null=True, blank=True)
    currency = models.CharField(max_length=20, default='NGN')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.status} - {self.user.username} - {self.cart.cart_code}'

class Country(models.Model):
    country = models.CharField(max_length=255, null=True, blank=True)
    country_code = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.country

