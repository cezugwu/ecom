from django.urls import path
from . import views

urlpatterns = [
    path('products/', views.products),
    path('country/', views.getcountry),
    path('search/', views.searchproducts),
    path('product/<slug:slug>', views.product),
    path('add/', views.add),
    path('update/', views.update),
    path('cart/', views.cart),
    path('deleteitem/', views.deleteitem),

    path('deleteitemu/', views.deleteitemu),
    path('addu/', views.addu),
    path('updateu/', views.updateu),
    path('cartu/', views.cartu),
    path('append/', views.append),
    path('getuser/', views.getuser),
    path('signup/', views.signup),

    path('createcartu/', views.createcartu),

    path('createcart/', views.createcart),
    path('deletecart/', views.deletecart), 

    path('shipinfo/', views.shipinfo),
    path('updateshipinfo/', views.updateshipinfo),
    path('getship/', views.getship),

    path('flutter/', views.flutter),
    path('fluttercall/', views.fluttercall),
    path('paystack/', views.paystack),
    path('vpaystack/',views.vpaystack),
]