from django.shortcuts import render, get_object_or_404
from django.contrib.auth.hashers import make_password
from rest_framework.decorators import api_view, permission_classes
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Product, Cart, CartItem, TransactionFlutter, TransactionPaystack, Shipping, Country, Ship, Order
from .serializer import ProductSerializer, CartItemSerializer, CartSerializer, ShippingSerializer, UserSignUpSerializer, ShipSerializer
import uuid
from decimal import Decimal
from django.conf import settings
import requests
from rest_framework import status
from .filters import SearchProductFilter
from django.conf import settings

from django.contrib.auth import get_user_model
User = get_user_model()

@api_view(['POST'])
def signup(request):
    serializer = UserSignUpSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({'message':'user created'})
    return Response({'error':serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def products(request):
    qs = Product.objects.all()

    # Filter by category
    category = request.GET.get('category')
    if category:
        qs = qs.filter(category__icontains=category)

    # Search by title
    search = request.GET.get('search')
    if search:
        qs = qs.filter(title__icontains=search)

    serializer = ProductSerializer(qs, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def product(request, slug):
    product = get_object_or_404(Product, slug=slug)
    serializer = ProductSerializer(product)
    return Response(serializer.data)

@api_view(['GET'])
def cartitem(request):
    user = request.user if request.user.is_authenticated else None
    session_id = request.GET.get('session_id')

    try:
        if user:
            cart, _ = Cart.objects.get_or_create(user=user, session_id=None, paid=False)
        else:
            if not session_id:
                return Response({'message': 'session_id is not provided'})
            cart, _ = Cart.objects.get_or_create(user=None, session_id=session_id, paid=False)
    except Cart.DoesNotExist():
        return Response({'error':'cart does not exist'})
    
    serializer = CartSerializer(cart)
    return Response(serializer.data)

@api_view(['POST'])
def cartadd(request):
    user = request.user if request.user.is_authenticated else None
    session_id = request.data.get('session_id')
    slug = request.data.get('slug')
    quantity = int(request.data.get('quantity', 1))
    action = request.data.get('action', '')

    try:
        if user:
            cart, _ = Cart.objects.get_or_create(user=user, session_id=None, paid=False)
        else:
            if not session_id:
                return Response({'message': 'session_id is not provided'})
            cart, _ = Cart.objects.get_or_create(user=None, session_id=session_id, paid=False)
    except Cart.DoesNotExist():
        return Response({'error':'cart does not exist'})

    product = get_object_or_404(Product, slug=slug)
    cartitem, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': quantity}
    )

    if not created:
        if action:
            cartitem.quantity = quantity
        else:
            cartitem.quantity += quantity
        cartitem.save()
        
    serializer = CartItemSerializer(cartitem)
    return Response(serializer.data)

@api_view(['POST'])
def cartremove(request):
    user = request.user if request.user.is_authenticated else None
    session_id = request.data.get('session_id')
    slug = request.data.get('slug')
    quantity = int(request.data.get('quantity', 1))

    try:
        if user:
            cart, _ = Cart.objects.get_or_create(user=user, session_id=None, paid=False)
        else:
            if not session_id:
                return Response({'message': 'session_id is not provided'})
            cart, _ = Cart.objects.get_or_create(user=None, session_id=session_id, paid=False)
    except Cart.DoesNotExist():
        return Response({'error':'cart does not exist'})

    product = get_object_or_404(Product, slug=slug)
    cartitem = CartItem.objects.get(
        cart=cart,
        product=product,
    )

    if cartitem.quantity:
        if cartitem.quantity > 1:
            cartitem.quantity -= quantity
            cartitem.save()
        else:
            cartitem.delete()
    else:
        cartitem.delete()

    return Response({'message':'cartitem updated'})

@api_view(['POST'])
def cartdelete(request):
    user = request.user if request.user.is_authenticated else None
    session_id = request.data.get('session_id')
    slug = request.data.get('slug')

    try:
        if user:
            cart, _ = Cart.objects.get_or_create(user=user, session_id=None, paid=False)
        else:
            if not session_id:
                return Response({'message': 'session_id is not provided'})
            cart, _ = Cart.objects.get_or_create(user=None, session_id=session_id, paid=False)
    except Cart.DoesNotExist():
        return Response({'error':'cart does not exist'})

    product = get_object_or_404(Product, slug=slug)
    cartitem = CartItem.objects.get(
        cart=cart,
        product=product,
    )
    cartitem.delete()
    
    return Response({'message':'cartitem deleted'})

@api_view(['POST'])
def cartclear(request):
    user = request.user if request.user.is_authenticated else None
    session_id = request.data.get('session_id')

    try:
        if user:
            cart, _ = Cart.objects.get_or_create(user=user, session_id=None, paid=False)
        else:
            if not session_id:
                return Response({'message': 'session_id is not provided'})
            cart, _ = Cart.objects.get_or_create(user=None, session_id=session_id, paid=False)
    except Cart.DoesNotExist():
        return Response({'error':'cart does not exist'})

    cartitem = CartItem.objects.filter(
        cart=cart,
    )
    cartitem.delete()
    
    return Response({'message':'all cartitem deleted'})

@api_view(['GET'])
def orderitem(request):
    user = request.user if request.user.is_authenticated else None
    session_id = request.GET.get('session_id')

    if user:
        cart = Cart.objects.filter(user=user, session_id=None, paid=True)
    else:
        if not session_id:
            return Response({'message': 'session_id is not provided'})
        cart = Cart.objects.filter(user=None, session_id=session_id, paid=True)
    
    serializer = CartSerializer(cart, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def ship(request):
    user = request.user if request.user.is_authenticated else None
    session_id = request.GET.get('session_id')

    try:
        if user:
            ship, _ = Ship.objects.get_or_create(user=user, session_id=None)
        else:
            if not session_id:
                return Response({'message': 'session_id is not provided'})
            ship, _ = Ship.objects.get_or_create(user=None, session_id=session_id)
    except Ship.DoesNotExist():
        return Response({'error':'ship does not exist'})
    
    serializer = ShipSerializer(ship)
    return Response(serializer.data)

@api_view(['GET'])
def shippingcurrent(request):
    user = request.user if request.user.is_authenticated else None
    session_id = request.GET.get('session_id')

    if user:
        ship, _ = Ship.objects.get_or_create(user=user, session_id=None)
    else:
        if not session_id:
            return Response({'error': 'session_id is required'}, status=400)
        ship, _ = Ship.objects.get_or_create(user=None, session_id=session_id)

    shipping = Shipping.objects.filter(ship=ship, selected=True).first()

    if not shipping:
        return Response({'message': 'No selected shipping found'}, status=404)

    serializer = ShippingSerializer(shipping)
    return Response(serializer.data, status=200)

@api_view(['GET'])
def shippingid(request):
    user = request.user if request.user.is_authenticated else None
    session_id = request.GET.get('session_id')
    shipping_id = request.GET.get('shipping_id')

    if user:
        ship, _ = Ship.objects.get_or_create(user=user, session_id=None)
    else:
        if not session_id:
            return Response({'error': 'session_id is required'}, status=400)
        ship, _ = Ship.objects.get_or_create(user=None, session_id=session_id)

    shipping = Shipping.objects.get(ship=ship, id=shipping_id)

    if not shipping:
        return Response({'message': 'No selected shipping found'}, status=404)

    serializer = ShippingSerializer(shipping)
    return Response(serializer.data, status=200)

@api_view(['POST'])
def shipping(request):
    user = request.user if request.user.is_authenticated else None
    session_id = request.data.get('session_id')
    serializer = ShippingSerializer(data=request.data)

    if serializer.is_valid():
        if user:
            ship, _ = Ship.objects.get_or_create(user=user, session_id=None)
        else:
            if not session_id:
                return Response({'error': 'session_id is required'}, status=400)
            ship, _ = Ship.objects.get_or_create(user=None, session_id=session_id)

        shipping = Shipping.objects.create(
            ship=ship,
            **serializer.validated_data 
        )
        default = str(request.data.get("default")).lower() == "true"

        if default:
            shipping.default = True
        shipping.selected = True
        shipping.save()

        return Response(ShippingSerializer(shipping).data, status=201)
    
    return Response(serializer.errors, status=400)

@api_view(['PUT', 'PATCH'])
def shippingupdate(request):
    user = request.user if request.user.is_authenticated else None
    shipping_id = request.data.get('shipping_id')
    session_id = request.data.get('session_id')

    if not shipping_id:
        return Response({'error': 'shipping_id is required'}, status=400)

    if user:
        ship, _ = Ship.objects.get_or_create(user=user, session_id=None)
    else:
        if not session_id:
            return Response({'error': 'session_id is required'}, status=400)
        ship, _ = Ship.objects.get_or_create(user=None, session_id=session_id)

    try:
        shipping = Shipping.objects.get(id=shipping_id, ship=ship)
    except Shipping.DoesNotExist:
        return Response({'error': 'Shipping not found'}, status=404)

    serializer = ShippingSerializer(shipping, data=request.data, partial=True)

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=200)

    return Response(serializer.errors, status=400)

@api_view(['PUT', 'PATCH'])
def shippingtrue(request):
    user = request.user if request.user.is_authenticated else None
    session_id = request.data.get('session_id')
    shipping_id = request.data.get('shipping_id')
    default = request.data.get('default')

    if not shipping_id:
        return Response({'error': 'shipping_id is required'}, status=400)

    if user:
        ship, _ = Ship.objects.get_or_create(user=user, session_id=None)
    else:
        if not session_id:
            return Response({'error': 'session_id is required'}, status=400)
        ship, _ = Ship.objects.get_or_create(user=None, session_id=session_id)

    try:
        shipping = Shipping.objects.get(id=shipping_id, ship=ship)
        if default:
            shipping.default = True
        else:
            shipping.selected = True
        shipping.save()
    except Shipping.DoesNotExist:
        return Response({'error': 'Shipping not found'}, status=404)

    serializer = ShippingSerializer(shipping)
    return Response(serializer.data, status=200)


@api_view(['POST'])
def flutter(request):
    user = request.user if request.user.is_authenticated else None
    session_id = request.data.get('session_id')

    tx_ref = str(uuid.uuid4())
    currency = 'NGN'
    redirect_url = 'http://localhost:3000/zentro/#/pending'
    tax = Decimal('4.00')

    if user:
        cart, _ = Cart.objects.get_or_create(user=user, session_id=None, paid=False)
        ship, _ = Ship.objects.get_or_create(user=user, session_id=None)
    else:
        if not session_id:
            return Response({'error': 'session_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        cart, _ = Cart.objects.get_or_create(user=None, session_id=session_id, paid=False)
        ship, _ = Ship.objects.get_or_create(user=None, session_id=session_id)

    amount = sum([(item.quantity * item.product.price) for item in cart.cartitem.all()])
    total_amount = amount + tax

    shipping = Shipping.objects.get(ship=ship, selected=True)
    
    customer = {}
    customer = {'email': f'{shipping.email if shipping.email else ''}', 'name': f'{shipping.name if shipping.name else ''}'} 

    flutterwave_payload = {
        'tx_ref': tx_ref,
        'amount': float(total_amount),
        'currency': currency,
        'redirect_url': redirect_url,
        'customer': customer,
        'customizations': {
            'title': 'EMK-Xpress',
            'logo': 'https://yourdomain.com/static/logo.png'
        },
    }

    headers = {
        'Authorization': f'Bearer {settings.FLUTTER_SECRET_KEY}',
        'Content-Type': 'application/json',
    }
    print('what')

    try:
        response = requests.post(
            'https://api.flutterwave.com/v3/payments',
            json=flutterwave_payload,
            headers=headers,
            timeout=10
        )
        
        response_data = response.json()
        link = response_data.get('data', {}).get('link')
        if link:
            transaction = TransactionFlutter.objects.create(
                cart=cart,
                tx_ref=tx_ref,
                link=link,
                currency=currency,
                amount=total_amount,
            )

    except requests.RequestException as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    if response.status_code in [200, 201]:
        return Response(response_data, status=status.HTTP_200_OK)
    else:
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)


# ✅ SHARED FUNCTION: verify payment and create order
def verify_and_create_order(tx_ref, transaction_id):
    headers = {'Authorization': f'Bearer {settings.FLUTTER_SECRET_KEY}'}
    verify_url = f'https://api.flutterwave.com/v3/transactions/{transaction_id}/verify'

    try:
        response = requests.get(verify_url, headers=headers, timeout=10)
        data = response.json()
    except requests.RequestException:
        return {'ok': False, 'message': 'Network error contacting Flutterwave'}

    if data.get('status') != 'success':
        return {'ok': False, 'message': 'Failed to verify with Flutterwave'}

    transaction_data = data.get('data', {})
    transaction = get_object_or_404(TransactionFlutter, tx_ref=tx_ref)

    if (
        transaction_data.get('status') == 'successful' and
        float(transaction_data.get('amount', 0)) == float(transaction.amount) and
        transaction_data.get('currency') == transaction.currency
    ):
        # ✅ Update transaction
        transaction.status = 'completed'
        transaction.transaction_id = transaction_id
        transaction.save(update_fields=['status', 'transaction_id'])

        # ✅ Update cart
        cart = transaction.cart
        cart.paid = True
        cart.save(update_fields=['paid'])

        # ✅ Get shipping info
        if cart.user:
            ship = Ship.objects.filter(user=cart.user).first()
        else:
            ship = Ship.objects.filter(session_id=cart.session_id).first()

        shipping = Shipping.objects.filter(ship=ship, selected=True).first()

        # ✅ Gather product data
        products = [
            {
                "id": item.product.id,
                "name": item.product.title,
                "price": float(item.product.price),
                "quantity": item.quantity,
                "image": (
                    item.product.image.url 
                    if hasattr(item.product, "image") and item.product.image 
                    else f"{settings.STATIC_URL}default.jpg"
                ),
            }
            for item in cart.cartitem.all()
        ]

        # ✅ Create order (if not already)
        order, created = Order.objects.get_or_create(
            tx_ref=tx_ref,
            cart=cart,
            defaults={
                'full_name': shipping.name,
                'email': shipping.email,
                'phone': shipping.phone,
                'address': shipping.address,
                'city': shipping.city,
                'state': shipping.state,
                'zip_code': shipping.zip_code,
                'country': shipping.country,
                'products': products,
                'total_amount': cart.get_total_price(),
                'transaction_id': transaction_id,
                'payment_status': 'completed'
            }
        )

        if created:
            return {'ok': True, 'message': 'Order created successfully'}
        else:
            return {'ok': True, 'message': 'Order already exists'}

    return {'ok': False, 'message': 'Verification failed'}

@api_view(['POST'])
def fluttercall(request):
    tx_ref = request.data.get('tx_ref')
    transaction_id = request.data.get('transaction_id')
    payment_status = request.data.get('status')

    if not all([tx_ref, transaction_id, payment_status]):
        return Response({'message': 'Missing required fields'}, status=status.HTTP_400_BAD_REQUEST)

    if payment_status != 'completed':
        return Response({'message': 'Payment not completed'}, status=status.HTTP_400_BAD_REQUEST)

    result = verify_and_create_order(tx_ref, transaction_id)

    if result['ok']:
        return Response({'message': result['message']}, status=status.HTTP_200_OK)
    else:
        return Response({'message': result['message']}, status=status.HTTP_400_BAD_REQUEST)

# ✅ 2️⃣ Webhook endpoint (auto verify even if user doesn’t visit page)
@api_view(['POST'])
@csrf_exempt
def flutterwave_webhook(request):
    secret_hash = settings.FLUTTER_HASH_SECRET  # from Flutterwave dashboard
    signature = request.headers.get('verif-hash')

    # ✅ Ensure request came from Flutterwave
    if signature != secret_hash:
        return Response({'message': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)

    data = request.data
    tx_ref = data.get('txRef')
    transaction_id = data.get('id')
    status_ = data.get('status')

    if status_ == 'successful':
        result = verify_and_create_order(tx_ref, transaction_id)
        if result['ok']:
            return Response({'message': 'Order processed via webhook'}, status=status.HTTP_200_OK)

    return Response({'message': 'Webhook received'}, status=status.HTTP_200_OK)


@api_view(['POST'])
def paystack(request):
    try:
        username = request.data.get('username')
        currency = 'NGN'

        user = get_object_or_404(User, username=username)
        cart = get_object_or_404(Cart, user=user, paid=False)
        total = sum([(item.quantity * item.product.price) for item in cart.cartitem.all()])
        tax = Decimal('4.00')
        amount = total + tax

        amount_kobo = int(amount * 100)

        data = {
            'email': user.email,
            'amount': amount_kobo,
            'callback_url': 'http://localhost:3000/pending',
        }

        headers = {
            'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
            'Content-Type': 'application/json'
        }

        response = requests.post('https://api.paystack.co/transaction/initialize', json=data, headers=headers)
        data = response.json()
        if response.status_code == 200:
            transaction = TransactionPaystack.objects.create(
                reference=data['data']['reference'],
                access_code=data['data']['access_code'],
                amount=amount_kobo,
                user=user,
                cart=cart,
                currency=currency,
            )
            return Response(data, status=status.HTTP_200_OK)
        
        else:
            return Response(data, status=status.HTTP_400_BAD_REQUEST)

    except Exception as exception:
        return Response({'error': str(exception)}, status=400)
    
@api_view(['POST'])
def vpaystack(request):
    try:
        reference = request.data.get('reference')

        headers = {
            'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
            'Content-Type': 'application/json'
        }

        response = requests.get(f'https://api.paystack.co/transaction/verify/{reference}', headers=headers)
        data = response.json()
        if data['status']:
            transaction = get_object_or_404(TransactionPaystack, reference=reference)

            if (
                    data['data']['status'] == 'success' and 
                    data['data']['amount'] == int(transaction.amount) and
                    data['data']['currency'] == transaction.currency
                ):

                transaction.status = 'completed'
                transaction.transaction_id = data['data']['id']
                transaction.save()

                cart = transaction.cart
                cart.paid = True
                cart.save()

                return Response({
                    'message': 'Payment successful',
                    'submessage': 'You have successfully made a payment'
                }, status=200)

            else:
                return Response({
                    'message': 'Payment verification failed',
                    'submessage': 'We could not verify your payment yet'
                }, status=400)

        else:
            return Response({
                'message': 'Failed to verify transaction with paystack'
            }, status=400)
                    
    except Exception as exception:
        return Response({'error': str(exception)}, status=400)
