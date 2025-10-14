import django_filters
from .models import Product


class SearchProductFilter(django_filters.FilterSet):
    class Meta:
        model = Product
        fields = {
            'name': ['iexact', 'icontains'],
            'price': ['exact', 'lt', 'gt', 'range'],
            'category': ['iexact', 'icontains'],
        }