from django.shortcuts import render, get_object_or_404
from django.contrib.auth.hashers import make_password
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Product, Cart, CartItem, TransactionFlutter, TransactionPaystack, Shipping, Country
from .serializer import ProductSerializer, CartItemSerializer, CartSerializer, UserSerializer, ShippingSerializer, CountrySerializer
from django.contrib.auth.models import User
import uuid
from decimal import Decimal
from django.conf import settings
import requests
from rest_framework import status
from .filters import SearchProductFilter

#non users
@api_view(['GET'])
def getcountry(request):
    country_name = request.GET.get('country_name')
    country = get_object_or_404(Country, country=country_name)

    serializer = CountrySerializer(country)
    return Response(serializer.data)

@api_view(['GET'])
def products(request):
    product = Product.objects.all()

    serializer = ProductSerializer(product, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def searchproducts(request):
    product_filter = SearchProductFilter(request.GET, queryset=Product.objects.all())
    product = product_filter.qs

    serializer = ProductSerializer(product, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def product(request, slug):
    product = get_object_or_404(Product, slug=slug)
    serializer = ProductSerializer(product)

    return Response(serializer.data)

@api_view(['POST'])
def add(request):
    cart_code = request.data.get('cart_code')
    product_id = request.data.get('product_id')

    cart, created = Cart.objects.get_or_create(cart_code=cart_code, paid=False)
    product = get_object_or_404(Product, id=product_id)
    cartitem, created = CartItem.objects.get_or_create(cart=cart, product=product)
    cartitem.quantity += 1
    cartitem.save()

    serializer = CartItemSerializer(cartitem)
    return Response(serializer.data)

@api_view(['POST'])
def update(request):
    cart_code = request.data.get('cart_code')
    product_id = request.data.get('product_id')
    action = request.data.get('action')

    cart = get_object_or_404(Cart, cart_code=cart_code, paid=False)
    product = get_object_or_404(Product, id=product_id)
    cartitem, created = CartItem.objects.get_or_create(cart=cart, product=product)

    if action == 'add':
        cartitem.quantity += 1
        cartitem.save()

    elif action == 'minus':
        if cartitem.quantity > 1:
            cartitem.quantity -= 1
            cartitem.save() 
        else:
            cartitem.delete()
            
    elif action == 'remove':
        cartitem.delete()
    
    serializer = CartItemSerializer(cartitem)
    return Response(serializer.data)


@api_view(['GET'])
def cart(request):
    cart_code = request.GET.get('cart_code')
    cart = get_object_or_404(Cart, cart_code=cart_code, paid=False)
    serializer = CartSerializer(cart)
    return Response(serializer.data)

@api_view(['POST'])
def deleteitem(request):
    cart_code = request.data.get('cart_code')

    cart = get_object_or_404(Cart, cart_code=cart_code, paid=False)
    cartitem = CartItem.objects.filter(cart=cart)

    cartitem.delete()

    return Response({'message':'cart item deleted successfully'})

#users
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def deleteitemu(request):
    username = request.data.get('username')
    user = get_object_or_404(User, username=username)

    cart = get_object_or_404(Cart, user=user, paid=False)
    cartitem = CartItem.objects.filter(cart=cart)

    cartitem.delete()

    return Response({'message':'cart item deleted successfully'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def addu(request):
    username = request.data.get('username')
    user = get_object_or_404(User, username=username)
    product_id = request.data.get('product_id')

    cart, created = Cart.objects.get_or_create(user=user, paid=False)
    product = get_object_or_404(Product, id=product_id)
    cartitem, created = CartItem.objects.get_or_create(cart=cart, product=product)
    cartitem.quantity += 1
    cartitem.save()

    serializer = CartItemSerializer(cartitem)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def updateu(request):
    username = request.data.get('username')
    user = get_object_or_404(User, username=username)
    product_id = request.data.get('product_id')
    action = request.data.get('action')

    cart = get_object_or_404(Cart, user=user, paid=False)
    product = get_object_or_404(Product, id=product_id)
    cartitem, created = CartItem.objects.get_or_create(cart=cart, product=product)

    if action == 'add':
        cartitem.quantity += 1
        cartitem.save()

    elif action == 'minus':
        if cartitem.quantity > 1:
            cartitem.quantity -= 1
            cartitem.save() 
        else:
            cartitem.delete()
            
    elif action == 'remove':
        cartitem.delete()
    
    serializer = CartItemSerializer(cartitem)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def cartu(request):
    username = request.GET.get('username')
    user = get_object_or_404(User, username=username)
    cart = get_object_or_404(Cart, user=user, paid=False)
    serializer = CartSerializer(cart)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def append(request):
    products = request.data.get('products', [])
    username = request.data.get('username')
    user = get_object_or_404(User, username=username)
    cart, created = Cart.objects.get_or_create(user=user, paid=False)
    for item in products:
        product_id = item.get('id')
        quantity = item.get('quantity')

        product = get_object_or_404(Product, id=product_id)
        cartitem, created = CartItem.objects.get_or_create(cart=cart, product=product)

        cartitem.quantity = quantity
        cartitem.save()
    serializer = CartItemSerializer(cartitem)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getuser(request):
    username = request.GET.get('username')
    user = get_object_or_404(User, username=username)

    serializer = UserSerializer(user)
    return Response(serializer.data)

@api_view(['POST'])
def signup(request):
    username = request.data.get('username')
    first_name = request.data.get('first_name')
    last_name = request.data.get('last_name')
    email = request.data.get('email')
    password1 = request.data.get('password1')
    password2 = request.data.get('password2')

    if password1 != password2:
        return Response({'message':'password mismatch'})
    
    if User.objects.filter(username=username).exists():
        return Response({'message':'user with the username already exist'})
    
    user, created = User.objects.get_or_create(
        username=username,
        first_name=first_name,
        last_name=last_name,
        email=email,
        password=make_password(password1),
    )

    return Response({'message':'user created successfully'})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def shipinfo(request):
    address = request.data.get('address')
    city = request.data.get('city')
    state = request.data.get('state')
    zip_code = request.data.get('zip_code')
    phone = request.data.get('phone')
    username = request.data.get('username')
    country = request.data.get('country')
    phone_code = request.data.get('phone_code')
    contact_name = request.data.get('contact_name')
    user = get_object_or_404(User, username=username)

    if Shipping.objects.filter(user=user).exists():
        return Response({'message':'your shipping infor already exist go to settings to change it'})
    
    shipping, created = Shipping.objects.get_or_create(
        user=user,
        address=address,
        city=city,
        state=state,
        zip_code=zip_code,
        phone=phone,
        country=country,
        phone_code=phone_code,
        contact_name = contact_name,
    )

    return Response({'shiping':'created succesfully'})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getship(request):
    username = request.GET.get('username')
    user = get_object_or_404(User, username=username)
    shipping = get_object_or_404(Shipping, user=user)

    serializer = ShippingSerializer(shipping)
    return Response(serializer.data)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def updateshipinfo(request):
    address = request.data.get('address')
    city = request.data.get('city')
    state = request.data.get('state')
    zip_code = request.data.get('zip_code')
    phone = request.data.get('phone')
    country = request.data.get('country')
    phone_code = request.data.get('phone_code')
    contact_name = request.data.get('contact_name')
    username = request.user.username 
    

    user = get_object_or_404(User, username=username)

    shipping, created = Shipping.objects.get_or_create(user=user)

    shipping.address = address if address else shipping.address
    shipping.city = city if city else shipping.city
    shipping.state = state if state else shipping.state
    shipping.zip_code = zip_code if zip_code else shipping.zip_code
    shipping.phone = phone if phone else shipping.phone
    shipping.country = country if country else shipping.country
    shipping.phone_code = phone_code if phone_code else shipping.phone_code
    shipping.contact_name = contact_name if contact_name else shipping.contact_name
    shipping.save()

    return Response({'message': 'Shipping info updated successfully'})

    


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def createcartu(request):
    username = request.data.get('username')
    user = get_object_or_404(User, username=username)

    cart, created = Cart.objects.get_or_create(user=user, paid=False)

    serializer = CartSerializer(cart)
    return Response(serializer.data)


#complicated non user
@api_view(['POST'])
def createcart(request):
    cart_code = request.data.get('cart_code')

    cart, created = Cart.objects.get_or_create(cart_code=cart_code, paid=False)

    serializer = CartSerializer(cart)
    return Response(serializer.data)

@api_view(['POST'])
def deletecart(request):
    cart_code = request.data.get('cart_code')

    cart, created = Cart.objects.get_or_create(cart_code=cart_code, paid=False)
    cart.delete()

    return Response({'message':'cart deleted'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def flutter(request):
    try:
        username = request.data.get('username')

        user = get_object_or_404(User, username=username)
        
        tx_ref = str(uuid.uuid4())
        currency = 'NGN'
        redirect_url = 'http://localhost:3000/pending'
        tax = Decimal('4.00')

        cart = get_object_or_404(Cart, user=user, paid=False)

        amount = sum([(item.quantity * item.product.price) for item in cart.cartitem.all()])
        total_amount = amount + tax

        transaction = TransactionFlutter.objects.create(
            cart=cart,
            user=user,
            tx_ref=tx_ref,
            currency=currency,
            amount=total_amount,
        )

        flutterwave_payload = {
            'tx_ref': tx_ref,
            'amount': float(total_amount),
            'currency': currency,
            'redirect_url': redirect_url,
            'customer': {
                'email': user.email,
                'username': user.username,
            },
            'customizations': {
                'title': 'EMK-Xpress',
            },
        }

        headers = {
            'Authorization': f'Bearer {settings.FLUTTER_SECRET_KEY}',
            'Content-Type': 'application/json',
        }

        response = requests.post(
            'https://api.flutterwave.com/v3/payments',
            json=flutterwave_payload,
            headers=headers
        )
            
        if response.status_code == 200:
            return Response(response.json(), status=status.HTTP_200_OK)
        else:
            return Response(response.json(), status=status.HTTP_400_BAD_REQUEST)

    except requests.exceptions.RequestException as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    


@api_view(['POST'])
def fluttercall(request):
    status = request.data.get('status')
    tx_ref = request.data.get('tx_ref')
    transaction_id = request.data.get('transaction_id')

    if status == 'completed':
        headers = {
            'Authorization': f'Bearer {settings.FLUTTER_SECRET_KEY}',
        }

        response = requests.get(
            f'https://api.flutterwave.com/v3/transactions/{transaction_id}/verify',
            headers=headers
        )

        data = response.json() 
        if data['status'] == 'success':
            transaction = get_object_or_404(TransactionFlutter, tx_ref=tx_ref)

            if (
                data['data']['status'] == 'successful' and
                float(data['data']['amount']) == float(transaction.amount) and
                data['data']['currency'] == transaction.currency
            ):
                transaction.status = 'completed'
                transaction.transaction_id = transaction_id
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
                'message': 'Failed to verify transaction with Flutterwave'
            }, status=400)
    else:
        return Response({'message': 'Payment was not successful'}, status=400)
    

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
