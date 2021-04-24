import django_filters
from .models import Good
from .models import GoodsBrand
from .models import GoodsCategory

CHOICES = [
    ["name", "по алфавиту возр"],
    ["-name", "по алфавиту убыв"],
    ["id", "по id возр"],
    ["-id", "по id убыв"]
]


class GoodFilter(django_filters.FilterSet):
    sku = django_filters.CharFilter(lookup_expr='icontains')
    name = django_filters.CharFilter(lookup_expr='icontains')
    # brand = django_filters.ModelMultipleChoiceFilter(queryset=GoodsBrand.objects.all())
    # category = django_filters.ModelMultipleChoiceFilter(queryset=GoodsCategory.objects.all())
    ordering = django_filters.OrderingFilter(choices=CHOICES, required=True, empty_label=None, )

    class Meta:
        model = Good
        fields = ['sku', 'name']
