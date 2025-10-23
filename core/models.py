from django.db import models
from django.conf import settings
import secrets
import string
from cloudinary.models import CloudinaryField
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from decimal import Decimal

User = get_user_model()


class Product(models.Model):
    CATEGORY_CHOICES = (
        ('ELECTRONICS', 'Electronics'),
        ('JEWELRY', 'Jewelry'),
        ('CLOTHINGS', 'Clothings'),
    )

    title = models.CharField(max_length=255, blank=True, null=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = CloudinaryField('image_ecommerce', blank=True, null=True)
    category = models.CharField(max_length=255, choices=CATEGORY_CHOICES, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug and self.title:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title if self.title else None

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_id = models.CharField(max_length=255, null=True, blank=True)
    paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_total_items(self):
        total_quantity = sum(item.quantity for item in self.cartitem.all())
        return total_quantity
    
    def get_total_price(self):
        total_price = sum(item.get_price for item in self.cartitem.all())
        return total_price
    
    def get_flutter_link(self):
        transaction = self.transactionflutter.filter(status="pending").first()
        return transaction.link if transaction else None
    
    def __str__(self):
            return f"username:{self.user.username} - cart:{self.id}" if self.user else f"session_id: {self.session_id} - cart:{self.id}" 

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='cartitem')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product')
    quantity = models.PositiveBigIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    class Meta:
        unique_together = ('cart', 'product')
        ordering = ['-created_at']

    @property
    def get_price(self):
        return (self.product.price * self.quantity) if self.product else None

    def save(self, *args, **kwargs):
        if self.id:
            old = CartItem.objects.get(id=self.id)
            # Only cancel if quantity or product changed
            if old.quantity != self.quantity or old.product != self.product:
                transaction = self.cart.transactionflutter.first()
                if transaction and transaction.status == "pending":
                    transaction.status = "canceled"
                    transaction.save(update_fields=["status"])
        super().save(*args, **kwargs)


    def __str__(self):
        return f'{self.quantity} quantity of {self.product.title} in cart with {f'username: {self.cart.user}' if self.cart.user else f'session_id: {self.cart.session_id}'}'

class Ship(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='ships')
    session_id = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Ship for {self.user or self.session_id}"

class Shipping(models.Model):
    ship = models.ForeignKey(Ship, on_delete=models.CASCADE, related_name='shippings', null=True, blank=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    phone = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=255, null=True, blank=True)
    state = models.CharField(max_length=255, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    zip_code = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=255, null=True, blank=True)
    email = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    selected = models.BooleanField(default=False, null=True, blank=True)
    default = models.BooleanField(default=False, null=True, blank=True)  

    class Meta:
        ordering = ['-default', '-selected', '-created_at']

    def save(self, *args, **kwargs):
        if self.default:
            Shipping.objects.filter(ship=self.ship, default=True).exclude(pk=self.pk).update(default=False)

        if self.selected:
            Shipping.objects.filter(ship=self.ship, selected=True).exclude(pk=self.pk).update(selected=False)

        super().save(*args, **kwargs)
        
            # ✅ If there's no default shipping, make this one default
        if not Shipping.objects.filter(ship=self.ship, default=True).exists():
            self.default = True
            super().save(update_fields=["default"])

        # ✅ If there's no selected shipping, make this one selected
        if not Shipping.objects.filter(ship=self.ship, selected=True).exists():
            self.selected = True
            super().save(update_fields=["selected"])


    def __str__(self):
        if self.ship and self.ship.user:
            return f"Shipping information for user: {self.id} {self.ship.user.username}"
        elif self.ship and self.ship.session_id:
            return f"Shipping information for session_id: {self.id} {self.ship.session_id}"
        return "Shipping information (no owner)"

class TransactionFlutter(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='transactionflutter')
    tx_ref = models.CharField(max_length=255, unique=True)
    transaction_id = models.CharField(max_length=255, null=True, blank=True)
    link = models.CharField(max_length=2550, null=True, blank=True)
    currency = models.CharField(max_length=20, default='NGN')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.pk and self.status == "pending":
            other_pending = TransactionFlutter.objects.filter(
                cart=self.cart,
                status="pending"
            )

            for old_tx in other_pending:
                old_tx.status = "canceled"
                old_tx.save(update_fields=["status"])
                print(f"Canceled old transaction: {old_tx.tx_ref}")

        super().save(*args, **kwargs)

    def __str__(self):
        if self.cart.user:
            return f"{self.status} - username: {self.cart.user.username}"
        else:
            return f"{self.status} - session_id: {self.cart.session_id}"

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
        return f"{self.status}" f"username:{self.user.username}" if self.cart.user.username else f"session_id: {self.session_id}" 

class Country(models.Model):
    country = models.CharField(max_length=255, null=True, blank=True)
    country_code = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.country

class Order(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='orderitem', blank=True, null=True)
    # Buyer info
    full_name = models.CharField(max_length=255)
    email = models.CharField(max_length=255)
    phone = models.CharField(max_length=50)
    address = models.TextField()
    city = models.CharField(max_length=255)
    state = models.CharField(max_length=255)
    zip_code = models.CharField(max_length=20, null=True, blank=True)
    country = models.CharField(max_length=255, null=True, blank=True)

    # Cart details
    products = models.JSONField(default=list)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    # Payment
    tx_ref = models.CharField(max_length=255, null=True, blank=True)
    transaction_id = models.CharField(max_length=255, null=True, blank=True)
    payment_status = models.CharField(max_length=50, default='pending')  # pending | completed | failed

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order by {self.full_name} - {self.payment_status}"