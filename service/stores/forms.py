from django.forms import ModelForm
from django.forms import ModelChoiceField
from django.forms import Form
from django.forms import FileField
from django.forms import Textarea
from django.forms import TextInput
from django.forms import NumberInput
from django.forms import CheckboxSelectMultiple
from django.forms import MultipleChoiceField
from django.forms import Select
from django.forms import CharField
from django.forms import Form

from .models import Store
from .models import GoodsBrand
from .models import GoodsCategory
from .models import Good
from .models import Supplier
from .models import Warehouse
from .models import System
from .models import StockSetting
from .models import StoreWarehouse
from .models import Job
from .models import UserJob

from .helpers.suppliers import Parser
from .helpers.scheduler import Scheduler


class CreateStoreForm(ModelForm):
    class Meta:
        model = Store
        fields = ['name', 'store_type', 'status', 'description', 'marketplace', ]
        widgets = {
            'description': Textarea(attrs={'cols': 50, 'rows': 3}),
        }


class BatchUpdateGoodsBrandForm(ModelForm):
    class Meta:
        model = Good
        fields = ['brand', ]

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # noinspection PyUnresolvedReferences
        self.fields['brand'].queryset = GoodsBrand.objects.filter(user=user)
        self.fields['brand'].label = 'Выберите бренд:'


class CreateGoodsCategoryForm(ModelForm):
    class Meta:
        model = GoodsCategory
        fields = ['name', 'description', 'parent', ]
        widgets = {
            'description': Textarea(attrs={'cols': 50, 'rows': 3}),
        }


class BatchUpdateGoodsCategoryForm(ModelForm):
    class Meta:
        model = Good
        fields = ['category', ]

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # noinspection PyUnresolvedReferences
        self.fields['category'].queryset = GoodsCategory.objects.filter(user=user)
        self.fields['category'].label = 'Выберите категорию:'


class GoodGeneralForm(ModelForm):
    class Meta:
        model = Good
        fields = [
            'sku',
            'article',
            'name',
            'description',
            'brand',
            'category',
            'weight',
            'pack_width',
            'pack_length',
            'pack_height',
            'barcode',
        ]
        widgets = {
            'description': Textarea(attrs={'cols': 50, 'rows': 3}),
        }


class BatchGoodsUploadForm(Form):
    file = FileField(label='Выберите файл с номенклатурой')


class CreateSupplierForm(ModelForm):
    class Meta:
        model = Supplier
        fields = ['name', 'tin', 'contact', 'email', 'phone', 'description', ]
        phone_help_msg = 'Телефон, 10 цифр без "+7", например, 9267775588'
        widgets = {
            'phone': TextInput(attrs={
                'placeholder': phone_help_msg,
                'onkeydown': 'checkPhone(this)',
            }),
            'email': TextInput(attrs={'placeholder': 'sales@supplier.ru'}),
            'description': Textarea(attrs={'cols': 50, 'rows': 3}),
        }
        labels = {'phone': phone_help_msg}


class CreateWarehouseForm(ModelForm):
    class Meta:
        model = Warehouse
        fields = ['active', 'name', 'stores', 'kind', 'supplier', 'description', 'code', 'priority', 'stores']
        widgets = {
            'stores': CheckboxSelectMultiple,
            'kind': Select(attrs={
                'oninput': 'checkType(this)',
            }),
            'description': Textarea(attrs={'cols': 50, 'rows': 3}),
        }


class CreateSystemForm(ModelForm):
    class Meta:
        model = System
        fields = ['name', 'code', 'description', ]
        widgets = {
            'description': Textarea(attrs={'cols': 50, 'rows': 3}),
        }


class CreateStockSettingForm(ModelForm):
    class Meta:
        model = StockSetting
        fields = ['name', 'priority', 'content']
        widgets = {
            'priority': NumberInput(attrs={
                'onkeyup': 'validateNumberInputMinValue(this, 1)',
            }),
            'content': Textarea(attrs={
                'cols': 50,
                'rows': 3,
                'class': 'hidden',
            }),
        }


class DeleteSelectedStockSettingsForm(Form):
    selected_settings = CharField(max_length=100, label=None, required=False)
    widgets = {
        'selected_settings': TextInput(attrs={
            'class': 'selected-settings-input',
        })
    }


class CreateStoreWarehouseForm(ModelForm):
    class Meta:
        model = StoreWarehouse
        fields = ['name', 'code', 'description']
        widgets = {
            'description': Textarea(attrs={
                'cols': 50,
                'rows': 3,
            })
        }


class SportCategorySelectForm(Form):
    choices = [(k, v) for k, v in Parser.get_supplier_categories().items()]
    categories = MultipleChoiceField(label='Категории товаров', choices=choices,
                                     widget=CheckboxSelectMultiple, required=True)


class CreateUserJobForm(ModelForm):
    fr_choices = Scheduler.frequency_choices()
    frequency = CharField(label='Частота выполнения', widget=Select(choices=fr_choices), required=True)

    class Meta:
        model = UserJob
        fields = ['active', 'name', 'frequency', 'schedule', 'job', 'description', ]

        widgets = {
            'schedule': NumberInput(attrs={
                'value': Scheduler.min_frequency(),
                'min': Scheduler.min_frequency(),
                'max': Scheduler.max_frequency(),
            }),
            'description': Textarea(attrs={'cols': 50, 'rows': 3}),
        }
        labels = {
            'job': f'Системная задача по расписанию',
            'schedule': f'Значение частоты выполнения (от {Scheduler.min_frequency()} до {Scheduler.max_frequency()})',
        }

    # noinspection PyUnresolvedReferences
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['job'] = ModelChoiceField(queryset=Job.objects.all(), label='Системная задача по расписанию')


class UpdateUserJobForm(ModelForm):
    fr_choices = Scheduler.frequency_choices()
    frequency = CharField(label='Частота выполнения', widget=Select(choices=fr_choices), required=True)

    class Meta:
        model = UserJob
        fields = ['active', 'name', 'frequency', 'schedule', 'description', ]

        widgets = {
            'schedule': NumberInput(attrs={
                'value': Scheduler.min_frequency(),
                'min': Scheduler.min_frequency(),
                'max': Scheduler.max_frequency(),
            }),
            'description': Textarea(attrs={'cols': 50, 'rows': 3}),
        }
        labels = {
            'schedule': f'Значение частоты выполнения (от {Scheduler.min_frequency()} до {Scheduler.max_frequency()})',
        }
