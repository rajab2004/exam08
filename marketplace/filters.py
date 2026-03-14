import django_filters
from django.db.models import Q
from .models import Product, Category


class ProductFilter(django_filters.FilterSet):
    category = django_filters.CharFilter(method="filter_category")
    region = django_filters.CharFilter(field_name="region", lookup_expr="iexact")
    min_price = django_filters.NumberFilter(field_name="price", lookup_expr="gte")
    max_price = django_filters.NumberFilter(field_name="price", lookup_expr="lte")

    class Meta:
        model = Product
        fields = ["category", "region", "min_price", "max_price"]

    def filter_category(self, queryset, name, value):
        """
        category=slug yoki category=id
        """
        value = str(value).strip()
        if value.isdigit():
            return queryset.filter(category_id=int(value))
        return queryset.filter(category__slug=value)