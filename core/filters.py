import django_filters
from core.models import Product, Package


class ProductFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(field_name="price", lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name="price", lookup_expr='lte')
    min_stock = django_filters.NumberFilter(field_name="stock", lookup_expr='gte')
    max_stock = django_filters.NumberFilter(field_name="stock", lookup_expr='lte')

    class Meta:
        model = Product
        fields = ['name', 'type', 'is_active', 'price', 'stock']


class PackageFilter(django_filters.FilterSet):
    min_total_price = django_filters.NumberFilter(field_name="total_price", lookup_expr='gte')
    max_total_price = django_filters.NumberFilter(field_name="total_price", lookup_expr='lte')
    target_group = django_filters.MultipleChoiceFilter(
        choices=Package.AGE_GROUPS,
        method='filter_target_group'
    )

    def filter_target_group(self, queryset, name, value):
        if value:
            return queryset.filter(target_group__in=value)
        return queryset

    class Meta:
        model = Package
        fields = ['name', 'total_price', 'target_group']