import json
import os.path
from collections import defaultdict

from django.views.decorators.http import require_http_methods
from django.views.decorators.http import require_GET
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import UserPassesTestMixin

from django.views.generic import ListView
from django.views.generic import DetailView
from django.views.generic import CreateView
from django.views.generic import UpdateView
from django.views.generic import DeleteView

from django.http import JsonResponse
from django.urls import reverse_lazy
from django.shortcuts import render
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist

from .models import Store
from .models import StoreProperty
from .models import MarketplaceProperty

from .models import GoodsBrand
from .models import GoodsCategory
from .models import Good

from .models import Supplier
from .models import Warehouse
from .models import WarehouseType

from .models import Stock
from .models import System
from .models import StockSetting

# noinspection PyProtectedMember
from .helpers.common import _exc
# noinspection PyProtectedMember
from .helpers.common import _log
# from .helpers.common import _err
from .helpers.common import is_valid_email
from .helpers.common import is_valid_phone
from .helpers.common import strip_phone
from .helpers.common import format_phone
from .helpers.common import get_phone_error
from .helpers.common import get_email_error
from .helpers.common import get_supplier_warehouse_type
from .helpers.common import is_valid_supplier_choice
from .helpers.common import get_supplier_error
# from .helpers.common import time_tracker

from .helpers.xls_processer import ExcelProcesser
from .helpers.api import API
from .helpers.managers import StockManager
from .helpers.managers import get_stock_condition_types
from .helpers.managers import get_stock_condition_fields
from .helpers.managers import get_stock_include_types

from .forms import CreateStoreForm
from .forms import CreateGoodsCategoryForm
from .forms import GoodGeneralForm
from .forms import BatchUpdateGoodsBrandForm
from .forms import BatchUpdateGoodsCategoryForm
from .forms import BatchGoodsUploadForm
from .forms import CreateSupplierForm
from .forms import CreateWarehouseForm
from .forms import CreateSystemForm
from .forms import CreateStockSettingForm
from .forms import DeleteSelectedStockSettingsForm

BASE_URL = 'https://stl-market.ru'
ACTIVE_STORE_STATUS = 'подключен'


@require_POST
@login_required()
def batch_update_brand(request):
    user = request.user
    redirect_to = f'{reverse_lazy("goods-list")}'
    form = BatchUpdateGoodsBrandForm(user, request.POST)
    if form.is_valid():
        try:
            brand = form.cleaned_data['brand']
            goods_ids = request.POST['checked-goods-list']
            goods_ids = json.loads(goods_ids)
            goods_ids = map(lambda item: int(item), goods_ids)
            goods_ids = set(goods_ids)
            if not len(goods_ids):
                messages.error(request, 'Не выделены товары для изменения.')
                return redirect(redirect_to)

            # noinspection PyUnresolvedReferences
            goods = Good.objects.filter(pk__in=goods_ids)
            saved_ids = []
            for good in goods:
                if good.user != user:
                    continue
                good.brand = brand
                good.save()
                saved_ids.append(good.pk)
            brand = brand or ''
            messages.success(request, f'Установлен бренд "{brand}" для единиц номенклатуры: {len(saved_ids)}')
            return redirect(redirect_to)
        except Exception as err:
            err_msg = f'Не удалось записать данные в БД. {_exc(err)}'
            messages.error(request, err_msg)
            return redirect(redirect_to)

    messages.error(request, f'Форма заполнена неверно: {form.errors.as_data()}')
    return redirect(redirect_to)


@require_POST
@login_required()
def batch_update_category(request):
    user = request.user
    redirect_to = f'{reverse_lazy("goods-list")}'
    form = BatchUpdateGoodsCategoryForm(user, request.POST)
    if form.is_valid():
        try:
            category = form.cleaned_data['category']
            goods_ids = request.POST['checked-goods-list']
            goods_ids = json.loads(goods_ids)
            goods_ids = map(lambda item: int(item), goods_ids)
            goods_ids = set(goods_ids)
            if not len(goods_ids):
                messages.error(request, 'Не выделены товары для изменения.')
                return redirect(redirect_to)
            # noinspection PyUnresolvedReferences
            goods = Good.objects.filter(pk__in=goods_ids)
            saved_ids = []
            for good in goods:
                if good.user != user:
                    continue
                good.category = category
                good.save()
                saved_ids.append(good.pk)
            category = category or ''
            messages.success(request, f'Установлена категория "{category}" для единиц номенклатуры: {len(saved_ids)}')
            return redirect(redirect_to)
        except Exception as err:
            err_msg = f'Не удалось записать данные в БД. {_exc(err)}'
            messages.error(request, err_msg)
            return redirect(redirect_to)

    messages.error(request, f'Форма заполнена неверно: {form.errors.as_data()}')
    return redirect(redirect_to)


@require_http_methods(['GET', 'POST'])
@login_required()
def batch_goods_upload(request):
    if request.method == 'POST':
        form = BatchGoodsUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file_supported_formats = ('.xlsx',)
            filename = form.files['file'].name
            wrong_format = False
            extension = ''
            try:
                name, extension = os.path.splitext(filename)
                if extension not in file_supported_formats:
                    wrong_format = True
            except (IndexError, Exception):
                wrong_format = True

            if wrong_format:
                err_msg = f'Файл имеет неверное расширение. ' \
                          f'Поддерживаются расширения: {",".join(file_supported_formats)}'
                messages.error(request, err_msg)
                return redirect('goods-list')

            bytes_io = form.files['file'].file
            raw = bytes_io.read()
            excel_handler = ExcelProcesser()
            save_dir, filename = excel_handler.batch_goods_upload(raw, extension, request.user)
            messages.success(request, f'Файл обработан.')
            form = BatchGoodsUploadForm()
            context = {
                'form': form,
                'title': 'Загрузка товаров из файла',
                'filename': f'{save_dir}&&{filename}',
            }
            return render(request, 'stores/good/goods_batch_upload.html', context=context)
        messages.error(request, f'Форма заполнена неверно: {form.errors.as_data()}')
        return redirect('goods-batch-upload')
    form = BatchGoodsUploadForm()
    context = {
        'form': form,
        'title': 'Загрузка товаров из файла'
    }
    return render(request, 'stores/good/goods_batch_upload.html', context=context)


@require_GET
@login_required()
def batch_goods_upload_success_file(request, path):
    excel_handler = ExcelProcesser()
    result, error = excel_handler.get_file_content(path)
    if error:
        messages.error(request, error)
        return redirect('goods-batch-upload')
    return result


@require_GET
@login_required()
def export_goods(request):
    return_view = 'goods-list'
    view = GoodListView()
    view.request = request
    qs = view.get_queryset()
    if not len(qs):
        messages.error(request, "Нет товаров для выгрузки. Измените фильтры.")
        return redirect(return_view)
    xls_handler = ExcelProcesser()
    result, error = xls_handler.export_goods(qs)
    if error:
        messages.error(request, error)
        return redirect(return_view)
    return result


# fake date manipulation
# good
@login_required()
def gen_goods(request, count=100):
    max_items = 5000
    count = max_items if count > max_items else count
    import uuid
    user = request.user
    for i in range(count):
        sku = str(uuid.uuid4())
        _good = {
            'sku': sku,
            'name': f'Товар # {str(i + 1)} ({sku[:10]})',
            'user': user
        }
        good = Good(**_good)
        good.save()
        _log(f'created good # {i + 1}')
    messages.success(request, f'Создано тестовых товаров: {count}')
    return redirect('goods-list')


@login_required()
def drop_goods(request):
    deleted_count = 0
    pattern = 'Товар #'
    # noinspection PyUnresolvedReferences
    for item in Good.objects.filter(user=request.user):
        if item.name.startswith(pattern):
            item.delete()
            deleted_count += 1
            _log(f'deleted good # {deleted_count}')
    messages.success(request, f'Удалено тестовых товаров: {deleted_count}')
    return redirect('goods-list')


# supplier
@login_required()
def gen_suppliers(request, count=100):
    max_items = 1000
    count = max_items if count > max_items else count
    import uuid
    user = request.user
    for i in range(count):
        _uuid = str(uuid.uuid4())
        _obj = {
            'name': f'Поставщик # {str(i + 1)} ({_uuid[:15]})',
            'tin': '77456645238',
            'email': f'sales@supplier_{i + 1}.ru',
            'phone': '+74957778855',
            'user': user
        }
        obj = Supplier(**_obj)
        obj.save()
    messages.success(request, f'Создано тестовых поставщиков: {count}')
    return redirect('suppliers-list')


@login_required()
def drop_suppliers(request):
    deleted_count = 0
    pattern = 'Поставщик #'
    # noinspection PyUnresolvedReferences
    for item in Supplier.objects.filter(user=request.user):
        if item.name.startswith(pattern):
            item.delete()
            deleted_count += 1
    messages.success(request, f'Удалено тестовых поставщиков: {deleted_count}')
    return redirect('suppliers-list')


# stock
@login_required()
def gen_stock(request):
    redirect_to = 'stock-list'
    good_name_pattern = 'Товар #'
    user = request.user
    # noinspection PyUnresolvedReferences
    whs = Warehouse.objects.filter(user=user).filter(supplier__isnull=True)
    if not len(whs):
        messages.error(request, 'Создайте минимум 1 собственный склад и повторите попытку.')
        return redirect(redirect_to)

    # noinspection PyUnresolvedReferences
    goods = Good.objects.filter(user=user).filter(name__startswith=good_name_pattern)
    if not len(goods):
        messages.error(request, 'Создайте минимум 1 тестовый товар и повторите попытку.')
        return redirect(redirect_to)

    import random
    count = 0
    for wh in whs:
        for good in goods:
            _dict = {
                'warehouse': wh,
                'good': good,
                'amount': random.randint(1, 1000),
                'user': user
            }
            row = Stock(**_dict)
            row.save()
            count += 1
            _log(f'created stock row # {count}')
    messages.success(request, f'Создано тестовых записей об остатках: {count}')
    return redirect(redirect_to)


@login_required()
def drop_stock(request):
    deleted_count = 0
    pattern = 'Товар #'
    # noinspection PyUnresolvedReferences
    for row in Stock.objects.filter(user=request.user):
        if row.good.name.startswith(pattern):
            row.delete()
            deleted_count += 1
            _log(f'deleted stock row # {deleted_count}')
    messages.success(request, f'Удалено тестовых записей об остатках: {deleted_count}')
    return redirect('stock-list')


# utils
def _qs_filtered_by_user(model, user, limit=None):
    if limit is None:
        qs = model.objects.filter(user=user)
    else:
        qs = model.objects.filter(user=user)[:limit]
    return qs


def _filter_qs(qs, user):
    return qs.filter(user=user).order_by('id')


def _filter_user_brands(context, request):
    # noinspection PyUnresolvedReferences,PyTypeChecker
    qs = _qs_filtered_by_user(model=GoodsBrand, user=request.user)
    context['form'].fields['brand'].queryset = qs


def _csv_to_list(csv_string):
    items = [int(_id) if _id.isnumeric() else None for _id in csv_string.split(',')]
    return items


def _get_supplier_warehouse_type_id():
    name = get_supplier_warehouse_type()
    # noinspection PyUnresolvedReferences
    rows = WarehouseType.objects.filter(name__iexact=name)
    if not len(rows):
        return
    return rows[0].pk


def _special_attrs():
    _dict = {
        'Покупки.Yandex.Market': [
            'store_api_url',
        ]
    }
    return _dict


def _get_pages_list(page_obj):
    return [page_num for page_num in range(1, page_obj.paginator.num_pages + 1)
            if page_num == 1 or not page_num % 10 or page_num == page_obj.paginator.num_pages]


def _get_model_list_title(model):
    # noinspection PyProtectedMember
    return model._meta.verbose_name_plural


def _get_store_api_url(store_id):
    return f'{BASE_URL}/{API.get_api_full_path()}/stores/{store_id}'


def is_active_store(store):
    return store.status.name.lower() == ACTIVE_STORE_STATUS


def get_store_by_id(store_id, user):
    err_msg = f'неверный id магазина: {store_id}'
    if not isinstance(store_id, int):
        return None, err_msg
    # noinspection PyUnresolvedReferences
    rows = Store.objects.filter(user=user).filter(id=store_id)
    if not len(rows):
        return None, err_msg

    store = rows[0]
    if not is_active_store(store):
        return None, f'Магазин {store.name} не активен, настройки доступны только для активных магазинов.'

    return store, None


# noinspection PyUnresolvedReferences
def get_store_stock_settings(store):
    if store is None:
        return
    rows = StockSetting.objects.filter(user=store.user).filter(store=store)
    return rows


def is_stock_settings_priority_used(priority, store, skip_setting_id=None):
    rows = get_store_stock_settings(store=store)
    if skip_setting_id:
        is_used = any(row.priority == priority for row in rows if row.id != skip_setting_id)
    else:
        is_used = any(row.priority == priority for row in rows)
    return is_used


# STORE
class StoreListView(LoginRequiredMixin, ListView):
    template_name = 'stores/store/list_stores.html'
    model = Store
    context_object_name = 'items'
    ordering = ['id']

    def get_queryset(self):
        # noinspection PyUnresolvedReferences
        qs = Store.objects.filter(user=self.request.user).order_by('id')
        for row in qs:
            setattr(row, 'is_active', is_active_store(row))
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['items_count'] = len(context['items'])
        context['title'] = 'Магазины'
        return context


@login_required()
@require_http_methods(['GET', 'POST'])
def add_store(request):
    if request.method == 'POST':
        form = CreateStoreForm(request.POST)
        form.instance.user = request.user
        if form.is_valid():
            form.save()
            store_id = form.instance.id

            # save props
            unwanted_fields = ['encoding', 'csrfmiddlewaretoken', ] + list(form.cleaned_data.keys())
            marketplace = form.cleaned_data['marketplace']
            form_data = dict(form.data)

            # TODO - use better condition
            if marketplace.name == 'Покупки.Yandex.Market':
                attr_name = 'store_api_url'
                store_api_url = _get_store_api_url(store_id)
                form_data[attr_name] = store_api_url

            for attr_name, value in form_data.items():
                if attr_name in unwanted_fields:
                    continue
                # noinspection PyUnresolvedReferences
                _property = MarketplaceProperty.objects.filter(name=attr_name).filter(marketplace=marketplace)[0]
                store = form.instance
                store_prop_instance = StoreProperty(
                    store=store,
                    property=_property,
                    value=value[0] if isinstance(value, list) else value
                )
                store_prop_instance.save()

            messages.success(request, f'Магазин "{form.instance.name}" успешно добавлен.')
            return redirect('stores-detail', pk=store_id)
        messages.error(request, f'Форма заполнена неверно: {form.errors.as_data()}')
        return redirect('stores-add')
    else:
        form = CreateStoreForm()
        props = defaultdict(list)
        special_attrs = _special_attrs()
        # noinspection PyUnresolvedReferences
        for row in MarketplaceProperty.objects.all():
            marketplace_name = row.marketplace.name
            # special attrs handling
            if row.name in special_attrs.get(marketplace_name, []):
                continue
            _dict = {
                'attr': row.name,
                'help': row.description,
                'mandatory': row.mandatory,
            }
            props[marketplace_name].append(_dict)
        context = {
            'form': form,
            'props': dict(props),
            'title': 'Добавление магазина'
        }
        return render(request, 'stores/store/add_store.html', context=context)


@login_required()
@require_GET
def view_store(request, pk):
    try:
        # noinspection PyUnresolvedReferences
        store = Store.objects.get(pk=pk)
    except ObjectDoesNotExist:
        messages.error(request, f'Не найден магазин с id {pk}.')
        return redirect('stores-list')
    except Exception as err:
        messages.error(request, f'Не удалось выполнить запрос к БД. {_exc(err)}')
        return redirect('stores-list')
    if store.user != request.user:
        messages.error(request, f'Магазин с id {pk} принадлежит другому пользователю сервиса.')
        return redirect('stores-list')

    # noinspection PyUnresolvedReferences
    store_props = StoreProperty.objects.filter(store=store)
    # noinspection PyUnresolvedReferences
    marketplace_props = MarketplaceProperty.objects.filter(marketplace=store.marketplace)
    props = []
    for prop in marketplace_props:
        _dict = {'attr': prop.name, 'help': prop.description, 'value': 'Не заполнено значение'}
        for _prop in store_props:
            if _prop.property.name == prop.name:
                _dict['value'] = _prop.value
                break
        props.append(_dict)

    context = {
        'item': store,
        'is_active': is_active_store(store),
        'props': props,
        'marketplace': store.marketplace.name,
        'title': 'Просмотр магазина',
    }
    return render(request, template_name='stores/store/detail_store.html', context=context)


@login_required()
@require_http_methods(['GET', 'POST'])
def update_store(request, pk):
    try:
        # noinspection PyUnresolvedReferences
        store = Store.objects.get(pk=pk)
    except ObjectDoesNotExist:
        messages.error(request, f'Не найден магазин с id {pk}.')
        return redirect('stores-list')
    except Exception as err:
        messages.error(request, f'Не удалось выполнить запрос к БД. {_exc(err)}')
        return redirect('stores-list')
    if store.user != request.user:
        messages.error(request, f'Магазин с id {pk} принадлежит другому пользователю сервиса.')
        return redirect('stores-list')

    if request.method == 'POST':
        copied_post = request.POST.copy()
        copied_post['marketplace'] = store.marketplace.pk
        form = CreateStoreForm(copied_post, instance=store)
        if form.is_valid():
            form.save()
            # save props
            unwanted_fields = ['encoding', 'csrfmiddlewaretoken', ] + list(form.cleaned_data.keys())
            marketplace = form.cleaned_data['marketplace']
            form_data = dict(form.data)

            # delete old props values from db
            # noinspection PyUnresolvedReferences
            StoreProperty.objects.filter(store=store).delete()

            # save new props values to db
            for attr_name, value in form_data.items():
                if attr_name in unwanted_fields:
                    continue
                # noinspection PyUnresolvedReferences
                _property = MarketplaceProperty.objects.filter(name=attr_name).filter(marketplace=marketplace)[0]
                store = form.instance
                store_prop_instance = StoreProperty(
                    store=store,
                    property=_property,
                    value=value[0] if isinstance(value, list) else value
                )
                store_prop_instance.save()

            messages.success(request, f'Изменения успешно сохранены.')
            return redirect('stores-detail', pk=pk)
        messages.error(request, f'Форма заполнена неверно: {form.errors.as_data()}')
        return redirect('stores-update', pk=pk)
    else:
        # noinspection PyUnresolvedReferences
        store_props = StoreProperty.objects.filter(store=store)
        # noinspection PyUnresolvedReferences
        marketplace_props = MarketplaceProperty.objects.filter(marketplace=store.marketplace)
        props = []
        for prop in marketplace_props:
            _dict = {'attr': prop.name, 'help': prop.description, 'mandatory': prop.mandatory, 'value': ''}
            for _prop in store_props:
                if _prop.property.name == prop.name:
                    _dict['value'] = _prop.value
                    break
            props.append(_dict)

        form = CreateStoreForm(instance=store)
        context = {
            'form': form,
            'props': props,
            'marketplace': store.marketplace.name,
            'title': 'Редактирование магазина',
        }
        return render(request, template_name='stores/store/update_store.html', context=context)


class StoreDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Store
    success_url = reverse_lazy('stores-list')
    template_name = 'stores/store/delete_store.html'

    def test_func(self):
        store = self.get_object()
        return self.request.user == store.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Удаление магазина'
        return context


# BRAND
class GoodsBrandListView(LoginRequiredMixin, ListView):
    template_name = 'stores/brand/list_brands.html'
    model = GoodsBrand
    context_object_name = 'items'
    ordering = ['id']

    def get_queryset(self):
        # noinspection PyUnresolvedReferences
        return GoodsBrand.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['items_count'] = len(context['items'])
        context['title'] = 'Бренды товаров'
        return context


class GoodsBrandCreateView(LoginRequiredMixin, CreateView):
    model = GoodsBrand
    fields = ['name', 'description']
    template_name = 'stores/brand/add_brand.html'

    def get_success_url(self):
        messages.success(self.request, f'Бренд "{self.object}" успешно создан')
        return reverse_lazy('brands-detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        name = form.cleaned_data['name']

        # validation
        # noinspection PyUnresolvedReferences
        qs = self.model.objects.filter(user=self.request.user)
        existing_rows = qs.filter(name__iexact=name)
        if len(existing_rows):
            existing_row = existing_rows[0]
            form.errors['Наименование не уникально'] = f'Найден элемент с id {existing_row.id} ' \
                                                       f'и наименованием {existing_row.name}'
            return self.form_invalid(form)

        form.instance.user = self.request.user
        return super().form_valid(form)

    def form_invalid(self, form):
        errors = ''.join(f'{k}: {v}. ' for k, v in form.errors.items())
        messages.error(self.request, f'Неверно заполнена форма. {errors}')
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Создание бренда'
        return context


class GoodsBrandDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = GoodsBrand
    fields = ['id', 'name', 'description']
    context_object_name = 'item'
    template_name = 'stores/brand/detail_brand.html'

    def form_valid(self, form):
        form.instance.user = self.request.user
        # noinspection PyUnresolvedReferences
        return super().form_valid(form)

    def test_func(self):
        brand = self.get_object()
        return brand.user == self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Просмотр бренда'
        return context


class GoodsBrandUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = GoodsBrand
    fields = ['name', 'description']
    template_name = 'stores/brand/update_brand.html'

    def test_func(self):
        brand = self.get_object()
        return brand.user == self.request.user

    def get_success_url(self):
        messages.success(self.request, f'Изменения успешно сохранены')
        return reverse_lazy('brands-detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        name = form.cleaned_data['name']

        # validation
        # noinspection PyUnresolvedReferences
        qs = self.model.objects.filter(user=self.request.user).exclude(id=form.instance.id)
        existing_rows = qs.filter(name__iexact=name)
        if len(existing_rows):
            existing_row = existing_rows[0]
            form.errors['Наименование не уникально'] = f'Найден элемент с id {existing_row.id} ' \
                                                       f'и наименованием {existing_row.name}'
            return self.form_invalid(form)

        return super().form_valid(form)

    def form_invalid(self, form):
        errors = ''.join(f'{k}: {v}. ' for k, v in form.errors.items())
        messages.error(self.request, f'Неверно заполнена форма. {errors}')
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Редактирование бренда'
        return context


class GoodsBrandDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = GoodsBrand
    success_url = reverse_lazy('brands-list')
    template_name = 'stores/brand/delete_brand.html'

    def test_func(self):
        store = self.get_object()
        return self.request.user == store.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Удаление бренда'
        return context


# CATEGORY
def _get_dependencies(source):
    dependencies = defaultdict(list)
    for item in source:
        _id = item['id']
        parent_id = item['parent_id']
        dependencies[parent_id].append(_id)
    return dependencies


def get_node(_id, source):
    if _id is None:
        return {"id": None}

    for item in source:
        if item['id'] == _id:
            return {
                "id": _id,
                "name": item['name']
            }
    raise ValueError(f'Wrong _id ({_id}) passed in to get_node method!')


def build_tree(node, dependencies, source):
    children = None
    if (node_id := node["id"]) in dependencies:
        for child in dependencies[node_id]:
            new_node = get_node(child, source)
            if children is None:
                children = []
            children.append(build_tree(new_node, dependencies, source))

    if children:
        node["childs"] = children
    node["childs_count"] = len(children) if children else 0
    return node


def _get_tree(user, add_empty_node=False):
    items = []
    if add_empty_node:
        node = {
            'id': 'empty',
            'name': 'Пустая категория',
            'parent': None,
            'parent_id': None,
        }
        items.append(node)
    # noinspection PyUnresolvedReferences
    for row in GoodsCategory.objects.filter(user=user):
        _dict = {
            'id': row.id,
            'name': row.name,
            'parent': row.parent.name if row.parent else None,
            'parent_id': row.parent.id if row.parent else None,
        }
        items.append(_dict)

    dependencies = _get_dependencies(items)
    root = get_node(None, items)
    build_tree(root, dependencies, items)
    return {
        'tree': root['childs'] if 'childs' in root else [],
        'items': items
    }


def _get_cats_tree(user, add_empty_node=False):
    # noinspection PyNoneFunctionAssignment
    items = _get_tree(user, add_empty_node).get('tree')
    return json.dumps(items, indent=4)


@login_required()
def get_categories_list(request):
    result = _get_tree(request.user)
    tree = result.get('tree')
    items = result.get('items')
    context = {
        'items': json.dumps(tree, indent=4),
        'items_count': len(items),
        'title': 'Категории товаров',
    }
    return render(request, template_name='stores/category/list_categories.html', context=context)


class GoodsCategoryCreateView(LoginRequiredMixin, CreateView):
    model = GoodsCategory
    form_class = CreateGoodsCategoryForm
    template_name = 'stores/category/add_category.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['parent_select_list'] = _get_cats_tree(self.request.user)

        context['title'] = 'Создание категории'
        return context

    def get_success_url(self):
        messages.success(self.request, f'Категория "{self.object}" успешно создана')
        return reverse_lazy('categories-list')

    def form_valid(self, form):
        name = form.cleaned_data['name']

        # validation
        # noinspection PyUnresolvedReferences
        qs = self.model.objects.filter(user=self.request.user)
        existing_rows = qs.filter(name__iexact=name)
        if len(existing_rows):
            existing_row = existing_rows[0]
            form.errors['Наименование не уникально'] = f'Найден элемент с id {existing_row.id} ' \
                                                       f'и наименованием {existing_row.name}'
            return self.form_invalid(form)

        form.instance.user = self.request.user
        return super().form_valid(form)

    def form_invalid(self, form):
        errors = ''.join(f'{k}: {v}. ' for k, v in form.errors.items())
        messages.error(self.request, f'Неверно заполнена форма. {errors}')
        return super().form_invalid(form)


class GoodsCategoryUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = GoodsCategory
    form_class = CreateGoodsCategoryForm
    template_name = 'stores/category/update_category.html'

    def test_func(self):
        item = self.get_object()
        return item.user == self.request.user

    def get_success_url(self):
        messages.success(self.request, f'Изменения успешно сохранены')
        return reverse_lazy('categories-list')

    def form_valid(self, form):
        name = form.cleaned_data['name']

        # validation
        # noinspection PyUnresolvedReferences
        qs = self.model.objects.filter(user=self.request.user).exclude(id=form.instance.id)
        existing_rows = qs.filter(name__iexact=name)
        if len(existing_rows):
            existing_row = existing_rows[0]
            form.errors['Наименование не уникально'] = f'Найден элемент с id {existing_row.id} ' \
                                                       f'и наименованием {existing_row.name}'
            return self.form_invalid(form)

        return super().form_valid(form)

    def form_invalid(self, form):
        errors = ''.join(f'{k}: {v}. ' for k, v in form.errors.items())
        messages.error(self.request, f'Неверно заполнена форма. {errors}')
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['parent_select_list'] = _get_cats_tree(self.request.user)
        context['parent_id'] = context['object'].parent_id or ''
        context['title'] = 'Редактирование категории'
        return context


class GoodsCategoryDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = GoodsCategory
    success_url = reverse_lazy('categories-list')
    template_name = 'stores/category/delete_category.html'

    def test_func(self):
        item = self.get_object()
        return item.user == self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Удаление категории'
        return context


# GOOD
class GoodListView(LoginRequiredMixin, ListView):
    template_name = 'stores/good/list_goods.html'
    model = Good
    context_object_name = 'items'
    ordering = ['id']
    paginate_by = 50

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._full_qs = None
        self._request_qs = None

    def _get_queryset_by_user(self):
        if self._full_qs is None:
            # noinspection PyUnresolvedReferences
            self._full_qs = self.model.objects.filter(user=self.request.user)
        return self._full_qs

    def get_queryset(self):
        if self._request_qs is None:
            full_queryset = self._get_queryset_by_user()
            queryset = None
            params = self.request.GET

            # brands
            brands = params.get('brands')
            brands = brands or None
            if brands:
                brands = _csv_to_list(brands)
                if None in brands:
                    queryset = full_queryset.filter(brand_id__in=brands) | full_queryset.filter(brand__isnull=True)
                else:
                    queryset = full_queryset.filter(brand_id__in=brands)

            # categories
            categories = params.get('cats')
            categories = categories or None
            if categories:
                if queryset is None:
                    queryset = full_queryset
                categories = _csv_to_list(categories)
                if None in categories:
                    queryset = queryset.filter(category_id__in=categories) | queryset.filter(category__isnull=True)
                else:
                    queryset = queryset.filter(category_id__in=categories)

            if queryset is None:
                queryset = full_queryset
            self._request_qs = queryset

        return self._request_qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        context['items_count'] = self._get_queryset_by_user().count()
        qs = self.get_queryset()
        context['filtered_items_count'] = qs.count()

        context['title'] = 'Товары'
        context['batch_update_brand_form'] = BatchUpdateGoodsBrandForm(user)
        context['batch_update_category_form'] = BatchUpdateGoodsCategoryForm(user)
        context['categories_list'] = _get_cats_tree(user)

        # data for filters
        # noinspection PyTypeChecker
        brands = _qs_filtered_by_user(GoodsBrand, user)
        brands = [{'id': item.pk, 'name': item.name, 'checked': False} for item in brands]
        brands.insert(0, {'id': None, 'name': 'Пустой бренд', 'checked': False})

        context['page_filter'] = ''
        if brands_filter := self.request.GET.get('brands'):
            context['page_filter'] += f'&brands={brands_filter}'
            brands_filter_list = _csv_to_list(brands_filter)
            for _dict in brands:
                _dict['checked'] = _dict['id'] in brands_filter_list
        brands = json.dumps(brands, ensure_ascii=False)
        context['brands_filter_source'] = brands

        if categories_filter := self.request.GET.get('cats'):
            context['page_filter'] += f'&cats={categories_filter}'
        context['categories_filter_source'] = _get_cats_tree(user, add_empty_node=True)
        context['pages'] = _get_pages_list(context['page_obj'])

        # stock
        _qs = context[self.context_object_name]
        if _qs.count():
            skus = [good.sku for good in _qs]
            stocks = StockManager().calculate_stock_by_stores(user, skus)
            context['stocks'] = stocks

        return context


class GoodCreateView(LoginRequiredMixin, CreateView):
    model = Good
    form_class = GoodGeneralForm
    template_name = 'stores/good/add_good.html'

    def get_success_url(self):
        messages.success(self.request, f'Товар "{self.object}" успешно создан')
        return reverse_lazy('goods-detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        sku = form.cleaned_data['sku']

        # noinspection PyUnresolvedReferences
        existing_rows = self.model.objects.filter(user=self.request.user).filter(sku__iexact=sku)
        if len(existing_rows):
            existing_row = existing_rows[0]
            form.errors['Код товара не уникален'] = f'Найден элемент с id {existing_row.id} ' \
                                                    f'и кодом {existing_row.sku}'
            return self.form_invalid(form)

        form.instance.user = self.request.user
        return super().form_valid(form)

    def form_invalid(self, form):
        errors = ''.join(f'{k}: {v}. ' for k, v in form.errors.items())
        messages.error(self.request, f'Неверно заполнена форма. {errors}')
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories_list'] = _get_cats_tree(self.request.user)
        context['title'] = 'Создание товара'
        _filter_user_brands(context=context, request=self.request)
        return context


class GoodDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
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
        'date_created',
        'date_updated',
    ]
    context_object_name = 'item'
    template_name = 'stores/good/detail_good.html'

    def form_valid(self, form):
        form.instance.user = self.request.user
        # noinspection PyUnresolvedReferences
        return super().form_valid(form)

    def test_func(self):
        brand = self.get_object()
        return brand.user == self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Просмотр товара'
        return context


class GoodUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Good
    form_class = GoodGeneralForm
    template_name = 'stores/good/update_good.html'

    def test_func(self):
        item = self.get_object()
        return item.user == self.request.user

    def get_success_url(self):
        messages.success(self.request, f'Изменения успешно сохранены')
        return reverse_lazy('goods-detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        sku = form.cleaned_data['sku']

        # validation
        # noinspection PyUnresolvedReferences
        qs = self.model.objects.filter(user=self.request.user).exclude(id=form.instance.id)
        existing_rows = qs.filter(sku__iexact=sku)
        if len(existing_rows):
            existing_row = existing_rows[0]
            form.errors['Код не уникален'] = f'Найден элемент с id {existing_row.id} ' \
                                             f'и кодом {existing_row.sku}'
            return self.form_invalid(form)

        return super().form_valid(form)

    def form_invalid(self, form):
        errors = ''.join(f'{k}: {v}. ' for k, v in form.errors.items())
        messages.error(self.request, f'Неверно заполнена форма. {errors}')
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories_list'] = _get_cats_tree(self.request.user)
        context['category_id'] = context['object'].category_id or ''
        context['title'] = 'Редактирование товара'
        _filter_user_brands(context=context, request=self.request)
        return context


class GoodDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Good
    success_url = reverse_lazy('goods-list')
    template_name = 'stores/good/delete_good.html'

    def test_func(self):
        item = self.get_object()
        return item.user == self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Удаление товара'
        return context


# SUPPLIER
class SupplierListView(LoginRequiredMixin, ListView):
    template_name = 'stores/supplier/list_suppliers.html'
    model = Supplier
    context_object_name = 'items'
    ordering = ['id']

    def get_queryset(self):
        # noinspection PyUnresolvedReferences
        qs = self.model.objects.filter(user=self.request.user).order_by('id')
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['items_count'] = len(context['items'])
        context['title'] = 'Поставщики товаров'
        return context


class SupplierCreateView(LoginRequiredMixin, CreateView):
    model = Supplier
    form_class = CreateSupplierForm
    template_name = 'stores/supplier/add_supplier.html'

    def get_success_url(self):
        messages.success(self.request, f'Поставщик "{self.object.name}" успешно создан')
        return reverse_lazy('suppliers-detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        phone = form.cleaned_data['phone']
        email = form.cleaned_data['email']
        name = form.cleaned_data['name']

        # check phone
        if phone and not is_valid_phone(phone):
            form.errors.update(get_phone_error())
        form.instance.phone = format_phone(phone)

        # check email
        if email and not is_valid_email(email):
            form.errors.update(get_email_error())

        if len(form.errors):
            return self.form_invalid(form)

        # validation
        # noinspection PyUnresolvedReferences
        qs = self.model.objects.filter(user=self.request.user)
        # check name duplicate
        existing_rows = qs.filter(name__iexact=name)
        if len(existing_rows):
            existing_row = existing_rows[0]
            form.errors['Наименование не уникально'] = f'Найден элемент с id {existing_row.id} ' \
                                                       f'и наименованием {existing_row.name}'
            return self.form_invalid(form)

        form.instance.user = self.request.user
        return super().form_valid(form)

    def form_invalid(self, form):
        errors = ''.join(f'{k}: {v}. ' for k, v in form.errors.items())
        messages.error(self.request, f'Неверно заполнена форма. {errors}')
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Создание поставщика'
        return context


class SupplierDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Supplier
    fields = ['id', 'name', 'tin', 'contact', 'email', 'phone', 'description', ]
    context_object_name = 'item'
    template_name = 'stores/supplier/detail_supplier.html'

    def test_func(self):
        obj = self.get_object()
        return obj.user == self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Просмотр поставщика'
        return context


class SupplierUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Supplier
    form_class = CreateSupplierForm
    template_name = 'stores/supplier/update_supplier.html'
    context_object_name = 'item'

    def test_func(self):
        obj = self.get_object()
        return obj.user == self.request.user

    def get_success_url(self):
        messages.success(self.request, f'Изменения успешно сохранены')
        return reverse_lazy('suppliers-detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        phone = form.cleaned_data['phone']
        email = form.cleaned_data['email']
        name = form.cleaned_data['name']

        # check phone
        if phone and not is_valid_phone(phone):
            form.errors.update(get_phone_error())
        form.instance.phone = format_phone(phone)

        # check email
        if email and not is_valid_email(email):
            form.errors.update(get_email_error())

        if len(form.errors):
            return self.form_invalid(form)

        # check name duplicate
        # noinspection PyUnresolvedReferences
        qs = self.model.objects.filter(user=self.request.user).exclude(id=form.instance.id)
        existing_rows = qs.filter(name__iexact=name)
        if len(existing_rows):
            existing_row = existing_rows[0]
            form.errors['Наименование не уникально'] = f'Найден элемент с id {existing_row.id} ' \
                                                       f'и наименованием {existing_row.name}'
            return self.form_invalid(form)

        form.instance.user = self.request.user
        return super().form_valid(form)

    def form_invalid(self, form):
        errors = ''.join(f'{k}: {v}. ' for k, v in form.errors.items())
        messages.error(self.request, f'Неверно заполнена форма. {errors}')
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Редактирование поставщика'

        # handle phone
        if phone := context['form'].initial['phone']:
            context['form'].initial['phone'] = strip_phone(phone)

        return context


class SupplierDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Supplier
    success_url = reverse_lazy('suppliers-list')
    template_name = 'stores/supplier/delete_supplier.html'

    def test_func(self):
        obj = self.get_object()
        return obj.user == self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Удаление поставщика'
        return context


# WAREHOUSE
class WarehouseListView(LoginRequiredMixin, ListView):
    template_name = 'stores/warehouse/list_warehouses.html'
    model = Warehouse
    context_object_name = 'items'
    ordering = ['id']

    def get_queryset(self):
        # noinspection PyUnresolvedReferences
        qs = self.model.objects.filter(user=self.request.user).order_by('id')
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['items_count'] = len(context['items'])
        context['title'] = 'Склады'
        return context


class WarehouseCreateView(LoginRequiredMixin, CreateView):
    model = Warehouse
    form_class = CreateWarehouseForm
    template_name = 'stores/warehouse/add_warehouse.html'

    def get_success_url(self):
        messages.success(self.request, f'Склад "{self.object.name}" успешно создан')
        return reverse_lazy('warehouses-detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        name = form.cleaned_data['name']
        code = form.cleaned_data['code']
        kind = form.cleaned_data['kind']
        supplier = form.cleaned_data['supplier']

        # validation
        if not is_valid_supplier_choice(kind, supplier):
            form.errors.update(get_supplier_error())
            return self.form_invalid(form)

        # noinspection PyUnresolvedReferences,PyUnresolvedReferences,PyUnresolvedReferences
        qs = self.model.objects.filter(user=self.request.user)

        # check name duplicate
        existing_rows = qs.filter(name__iexact=name)
        if len(existing_rows):
            existing_row = existing_rows[0]
            form.errors['Наименование не уникально'] = f'Найден элемент с id {existing_row.id} ' \
                                                       f'и наименованием {existing_row.name}'
            return self.form_invalid(form)

        # check code duplicate
        existing_rows = qs.filter(code__iexact=code)
        if len(existing_rows):
            existing_row = existing_rows[0]
            form.errors['Код не уникален'] = f'Найден элемент с id {existing_row.id} ' \
                                             f'и кодом {existing_row.code}'
            return self.form_invalid(form)

        form.instance.user = self.request.user
        return super().form_valid(form)

    def form_invalid(self, form):
        errors = ''.join(f'{k}: {v}. ' for k, v in form.errors.items())
        messages.error(self.request, f'Неверно заполнена форма. {errors}')
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Создание склада'

        # filter supplier choice
        supplier_qs = context['form'].fields['supplier'].queryset
        supplier_qs = _filter_qs(supplier_qs, self.request.user)
        context['form'].fields['supplier'].queryset = supplier_qs

        # filter stores choice
        stores_qs = context['form'].fields['stores'].queryset
        context['form'].fields['stores'].queryset = _filter_qs(stores_qs, self.request.user)

        # prefill kind and supplier
        sid_arg = 'sid'
        if sid := self.request.GET.get(sid_arg):
            try:
                sid = int(sid)
            except ValueError:
                messages.error(self.request, f'Указан неверный id поставщика для создания склада (неверный тип): {sid}')
                return context

            try:
                _ = supplier_qs.get(pk=sid)
            except ObjectDoesNotExist:
                messages.error(self.request,
                               f'Указан неверный id поставщика для создания склада (не найден поставщик): {sid}')
                return context

            if kind_id := _get_supplier_warehouse_type_id():
                context['form'].initial['kind'] = kind_id
                context['form'].initial['supplier'] = sid
            else:
                messages.error(self.request,
                               f'В справочнике "Типы складов" (в админке) необходимо создать элемент с наименованием'
                               f' "{get_supplier_warehouse_type()}" и повторить попытку.')
                return context

        return context


class WarehouseDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Warehouse
    fields = ['id', 'name', 'active', 'kind', 'supplier', 'code', 'priority', 'description', ]
    context_object_name = 'item'
    template_name = 'stores/warehouse/detail_warehouse.html'

    def test_func(self):
        obj = self.get_object()
        return obj.user == self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Просмотр склада'
        return context


class WarehouseUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Warehouse
    form_class = CreateWarehouseForm
    template_name = 'stores/warehouse/update_warehouse.html'
    context_object_name = 'item'

    def test_func(self):
        obj = self.get_object()
        return obj.user == self.request.user

    def get_success_url(self):
        messages.success(self.request, f'Изменения успешно сохранены')
        return reverse_lazy('warehouses-detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        name = form.cleaned_data['name']
        code = form.cleaned_data['code']
        kind = form.cleaned_data['kind']
        supplier = form.cleaned_data['supplier']

        if not is_valid_supplier_choice(kind, supplier):
            form.errors.update(get_supplier_error())
            return self.form_invalid(form)

        # validation
        # noinspection PyUnresolvedReferences,PyUnresolvedReferences,PyUnresolvedReferences
        qs = self.model.objects.filter(user=self.request.user).exclude(id=form.instance.id)

        # check name duplicate
        existing_rows = qs.filter(name__iexact=name)
        if len(existing_rows):
            existing_row = existing_rows[0]
            form.errors['Наименование не уникально'] = f'Найден элемент с id {existing_row.id} ' \
                                                       f'и наименованием {existing_row.name}'
            return self.form_invalid(form)

        # check code duplicate
        existing_rows = qs.filter(code__iexact=code)
        if len(existing_rows):
            existing_row = existing_rows[0]
            form.errors['Код не уникален'] = f'Найден элемент с id {existing_row.id} ' \
                                             f'и кодом {existing_row.code}'
            return self.form_invalid(form)

        return super().form_valid(form)

    def form_invalid(self, form):
        errors = ''.join(f'{k}: {v}. ' for k, v in form.errors.items())
        messages.error(self.request, f'Неверно заполнена форма. {errors}')
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Редактирование склада'

        # filter supplier choice
        supplier_qs = context['form'].fields['supplier'].queryset
        context['form'].fields['supplier'].queryset = _filter_qs(supplier_qs, self.request.user)

        # filter stores choice
        stores_qs = context['form'].fields['stores'].queryset
        context['form'].fields['stores'].queryset = _filter_qs(stores_qs, self.request.user)

        return context


class WarehouseDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Warehouse
    success_url = reverse_lazy('warehouses-list')
    template_name = 'stores/warehouse/delete_warehouse.html'

    def test_func(self):
        obj = self.get_object()
        return obj.user == self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Удаление склада'
        return context


# STOCK
class StockListView(LoginRequiredMixin, ListView):
    template_name = 'stores/stock/list_stock.html'
    model = Stock
    context_object_name = 'items'
    paginate_by = 50
    ordering = ['id']

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._full_qs = None
        self._request_qs = None

    def _get_queryset_by_user(self):
        if self._full_qs is None:
            stock = StockManager().get_user_stock(self.request.user)
            self._full_qs = stock
        return self._full_qs

    def get_queryset(self):
        return self._get_queryset_by_user()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['items_count'] = len(self.get_queryset())
        context['pages'] = _get_pages_list(context['page_obj'])
        context['title'] = 'Остатки товаров'

        # warehouse
        wh_rows = _qs_filtered_by_user(Warehouse, self.request.user)
        whs = {row.id: {'type': row.kind.name, 'name': row.name} for row in wh_rows}
        context['whs'] = whs

        return context

    @staticmethod
    def add_to_dict(_dict, _id):
        _dict[_id] = f'extra for {_id}'


# SYSTEM
class SystemListView(LoginRequiredMixin, ListView):
    template_name = 'stores/system/list_systems.html'
    model = System
    context_object_name = 'items'
    ordering = ['id']

    def get_queryset(self):
        # noinspection PyUnresolvedReferences
        qs = self.model.objects.filter(user=self.request.user).order_by('id')
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['items_count'] = len(context['items'])
        # noinspection PyTypeChecker,PyTypeChecker
        context['title'] = _get_model_list_title(self.model)
        return context


class SystemCreateView(LoginRequiredMixin, CreateView):
    model = System
    form_class = CreateSystemForm
    template_name = 'stores/system/add_system.html'

    def get_success_url(self):
        messages.success(self.request, f'Учетная система "{self.object.name}" успешно создана')
        return reverse_lazy('systems-detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        name = form.cleaned_data['name']
        code = form.cleaned_data['code']

        # validation
        # noinspection PyUnresolvedReferences,PyUnresolvedReferences,PyUnresolvedReferences
        qs = self.model.objects.filter(user=self.request.user)

        # check name duplicate
        existing_rows = qs.filter(name__iexact=name)
        if len(existing_rows):
            existing_row = existing_rows[0]
            form.errors['Наименование не уникально'] = f'Найден элемент с id {existing_row.id} ' \
                                                       f'и наименованием {existing_row.name}'
            return self.form_invalid(form)

        # check code duplicate
        existing_rows = qs.filter(code__iexact=code)
        if len(existing_rows):
            existing_row = existing_rows[0]
            form.errors['Код не уникален'] = f'Найден элемент с id {existing_row.id} ' \
                                             f'и кодом {existing_row.code}'
            return self.form_invalid(form)

        form.instance.user = self.request.user
        return super().form_valid(form)

    def form_invalid(self, form):
        errors = '. '.join(f'{k}: {v}' for k, v in form.errors.items())
        messages.error(self.request, f'Неверно заполнена форма. {errors}')
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Создание учетной системы'
        return context


class SystemDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = System
    fields = ['id', 'name', 'code', 'token', 'description', ]
    context_object_name = 'item'
    template_name = 'stores/system/detail_system.html'

    def test_func(self):
        obj = self.get_object()
        return obj.user == self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Просмотр учетной системы'
        return context


class SystemUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = System
    form_class = CreateSystemForm
    template_name = 'stores/system/update_system.html'
    context_object_name = 'item'

    def test_func(self):
        obj = self.get_object()
        return obj.user == self.request.user

    def get_success_url(self):
        messages.success(self.request, f'Изменения успешно сохранены')
        return reverse_lazy('systems-detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        name = form.cleaned_data['name']
        code = form.cleaned_data['code']

        # validation
        # noinspection PyUnresolvedReferences,PyUnresolvedReferences,PyUnresolvedReferences
        qs = self.model.objects.filter(user=self.request.user).exclude(id=form.instance.id)

        # check name duplicate
        existing_rows = qs.filter(name__iexact=name)
        if len(existing_rows):
            existing_row = existing_rows[0]
            form.errors['Наименование не уникально'] = f'Найден элемент с id {existing_row.id} ' \
                                                       f'и наименованием {existing_row.name}'
            return self.form_invalid(form)

        # check code duplicate
        existing_rows = qs.filter(code__iexact=code)
        if len(existing_rows):
            existing_row = existing_rows[0]
            form.errors['Код не уникален'] = f'Найден элемент с id {existing_row.id} ' \
                                             f'и кодом {existing_row.code}'
            return self.form_invalid(form)

        return super().form_valid(form)

    def form_invalid(self, form):
        errors = ''.join(f'{k}: {v}. ' for k, v in form.errors.items())
        messages.error(self.request, f'Неверно заполнена форма. {errors}')
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Редактирование учетной системы'
        return context


class SystemDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = System
    success_url = reverse_lazy('systems-list')
    template_name = 'stores/system/delete_system.html'

    def test_func(self):
        obj = self.get_object()
        return obj.user == self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Удаление учетной системы'
        return context


# STOCK SETTING
class StockSettingListView(LoginRequiredMixin, ListView):
    template_name = 'stores/stock_setting/list_stock_settings.html'
    model = StockSetting
    context_object_name = 'items'
    ordering = ['id']
    _store = None

    def get(self, *args, **kwargs):
        redirect_to = redirect('stores-list')
        store_id = kwargs.get('store_pk')
        store, err = get_store_by_id(store_id, self.request.user)

        if err:
            messages.error(self.request, err)
            return redirect_to

        self._store = store
        return super().get(*args, **kwargs)

    def get_queryset(self):
        # noinspection PyUnresolvedReferences
        qs = self.model.objects.filter(user=self.request.user).filter(store=self._store).order_by('priority')
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['items_count'] = len(context['items'])
        # noinspection PyTypeChecker,PyTypeChecker
        context['title'] = f'{_get_model_list_title(self.model)} - {self._store.name}'
        context['store_name'] = self._store.name
        context['store_id'] = self._store.id
        context['batch_delete_form'] = DeleteSelectedStockSettingsForm()

        # stocks
        qs = context[self.context_object_name]
        user = self.request.user
        if qs.count():
            stocks = StockManager().get_user_stock(user)
            calculated_stock = StockManager.calculate_stock_by_store_settings(qs, stocks)
            context['calculated_stock_by_settings'] = calculated_stock['settings']
            context['calculated_stock_by_conditions'] = calculated_stock['conditions']

        context['setting_not_used_text'] = StockManager.get_setting_not_used_text()
        return context


class StockSettingCreateView(LoginRequiredMixin, CreateView):
    model = StockSetting
    form_class = CreateStockSettingForm
    template_name = 'stores/stock_setting/add_setting.html'
    _store = None

    def get(self, *args, **kwargs):
        if not hasattr(self, 'request'):
            return

        redirect_to = redirect('stores-list')
        store_id = kwargs.get('store_pk')
        store, err = get_store_by_id(store_id, self.request.user)

        if err:
            messages.error(self.request, err)
            return redirect_to

        self._store = store
        return super().get(*args, **kwargs)

    def get_success_url(self):
        messages.success(self.request, f'Настройка "{self.object.name}" успешно создана')
        # return reverse_lazy('stock-settings-list', kwargs={'store_pk': self._store.id})
        return reverse_lazy('stores-list')

    def form_valid(self, form):
        user = self.request.user
        store_id = self.kwargs.get('store_pk')

        # validation
        store, err = get_store_by_id(store_id, user)
        if err:
            form.errors['Указан неверный id магазина'] = err
            return self.form_invalid(form)
        self._store = store

        form_is_valid = True
        priority = form.cleaned_data['priority']
        content = form.cleaned_data['content']

        err = StockManager.validate_stock_setting_content(content, user)
        if err:
            form.errors['Проверка условий'] = err
            form_is_valid = False

        min_val = 1
        if priority < min_val:
            form.errors['Неверный порядок'] = f'Разрешены значения не меньше {min_val}'
            form_is_valid = False

        if is_stock_settings_priority_used(priority, store):
            form.errors['Не уникальный порядок'] = f'Найдена другая настройка с порядком {priority} ' \
                                                   f'для магазина {self._store.name}'
            form_is_valid = False

        if not form_is_valid:
            return self.form_invalid(form)

        form.instance.store = self._store
        form.instance.user = user

        return super().form_valid(form)

    def form_invalid(self, form):
        errors = '. '.join(f'{k}: {v}' for k, v in form.errors.items())
        messages.error(self.request, f'Неверно заполнена форма. {errors}')
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Создание настройки остатков'

        context['condition_types'] = _json(get_stock_condition_types())
        context['condition_fields'] = _json(get_stock_condition_fields())
        context['include_types'] = _json(get_stock_include_types())
        context['brands'] = get_brands_by_user(self.request.user)
        context['cats'] = _get_cats_tree(self.request.user)
        context['warehouses'] = get_warehouses_by_user(self.request.user)

        if self._store:
            context['title'] = f'{context["title"]} - {self._store.name}'
            context['store_name'] = self._store.name
            context['store_id'] = self._store.id
        return context


class StockSettingUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = StockSetting
    form_class = CreateStockSettingForm
    template_name = 'stores/stock_setting/update_setting.html'
    _store = None

    def test_func(self):
        obj = self.get_object()
        return obj.user == self.request.user

    def get_success_url(self):
        messages.success(self.request, f'Изменения успешно сохранены')
        # return reverse_lazy('stock-settings-list', kwargs={'store_pk': self.object.store.id})
        return reverse_lazy('stores-list')

    def form_valid(self, form):
        self._store = self.object.store

        # validation
        form_is_valid = True
        priority = form.cleaned_data['priority']
        content = form.cleaned_data['content']

        err = StockManager.validate_stock_setting_content(content, self.request.user)
        if err:
            form.errors['Проверка условий'] = err
            form_is_valid = False

        min_val = 1
        if priority < min_val:
            form.errors['Неверный порядок'] = f'Разрешены значения не меньше {min_val}'
            form_is_valid = False

        if is_stock_settings_priority_used(priority, self._store, form.instance.id):
            form.errors['Не уникальный порядок'] = f'Найдена другая настройка с порядком {priority} ' \
                                                   f'для магазина {self._store.name}'
            form_is_valid = False

        if not form_is_valid:
            return self.form_invalid(form)

        return super().form_valid(form)

    def form_invalid(self, form):
        errors = ''.join(f'{k}: {v}. ' for k, v in form.errors.items())
        messages.error(self.request, f'Неверно заполнена форма. {errors}')
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        self._store = self.object.store
        context = super().get_context_data(**kwargs)
        context['title'] = f'Редактирование настройки остатков'

        context['condition_types'] = _json(get_stock_condition_types())
        context['condition_fields'] = _json(get_stock_condition_fields())
        context['include_types'] = _json(get_stock_include_types())
        context['brands'] = get_brands_by_user(self.request.user)
        context['cats'] = _get_cats_tree(self.request.user)
        context['warehouses'] = get_warehouses_by_user(self.request.user)

        if self._store:
            context['title'] = f'{context["title"]} - {self._store.name}'
            context['store_name'] = self._store.name
            context['store_id'] = self._store.id
        return context


class StockSettingDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = StockSetting
    template_name = 'stores/stock_setting/delete_setting.html'

    def get_success_url(self):
        return reverse_lazy('stock-settings-list', kwargs={'store_pk': self.object.store.id})

    def test_func(self):
        obj = self.get_object()
        return obj.user == self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Удаление настройки остатков'

        store = self.object.store
        context['title'] = f'{context["title"]} - {store.name}'
        context['store_name'] = store.name
        context['store_id'] = store.id
        return context


@require_POST
@login_required()
def stock_settings_batch_delete(request):
    user = request.user
    form = DeleteSelectedStockSettingsForm(request.POST)
    redirect_to = f'{reverse_lazy("stores-list")}'
    if form.is_valid():
        _ids = form.cleaned_data['selected_settings']
        if not _ids:
            messages.error(request, 'Не выделены настройки.')
            return redirect(redirect_to)
        _ids = _ids.split(',')
        _ids = set(_ids)

        try:
            _ids = map(lambda item: int(item), _ids)
        except (ValueError, Exception):
            messages.error(request, 'Не удалось прочитать выделенные настройки.')
            return redirect(redirect_to)

        deleted = 0
        # noinspection PyUnresolvedReferences
        rows = StockSetting.objects.filter(pk__in=_ids)

        for row in rows:
            if row.user != user:
                continue
            try:
                row.delete()
                deleted += 1
            except (ValueError, Exception) as err:
                err_msg = f'Не удалось удалить настройку с id {row.id}: {_exc(err)}'
                messages.error(request, err_msg)
                return redirect(redirect_to)

        messages.success(request, f'Удалено настроек: {deleted}')
        return redirect(redirect_to)

    messages.error(request, f'Форма заполнена неверно: {form.errors.as_data()}')
    return redirect(redirect_to)


@require_GET
@login_required()
def get_user_goods(request):
    rows = _qs_filtered_by_user(Good, request.user)
    if not len(rows):
        return JsonResponse(data=None, status=404, safe=False)
    items = [{'sku': row.sku, 'name': row.name, } for row in rows]
    return JsonResponse(data=items, status=200, safe=False)


def _json(obj):
    return json.dumps(obj, ensure_ascii=False)


# noinspection PyTypeChecker
def get_brands_by_user(user):
    rows = _qs_filtered_by_user(model=GoodsBrand, user=user)
    items = []
    for row in rows:
        _row = {
            'val': row.id,
            'text': row.name,
        }
        items.append(_row)
    return _json(items)


# noinspection PyTypeChecker
def get_warehouses_by_user(user):
    rows = _qs_filtered_by_user(model=Warehouse, user=user)
    rows = rows.filter(active=True)
    items = []
    for row in rows:
        _row = {
            'val': row.id,
            'text': row.name,
        }
        items.append(_row)
    return _json(items)


# API

# help page
@require_GET
def api_help(request):
    context = API().get_api_help()
    return render(request, 'stores/api/help.html', context=context)


# warehouse
@require_GET
def api_warehouse_list(request):
    return API().get_warehouse_list(request)


# noinspection PyUnusedLocal
@require_GET
def api_warehouse_list_help(request):
    return API().get_warehouse_list_help()


# category
@require_GET
def api_category_list(request):
    return API().get_category_list(request)


# noinspection PyUnusedLocal
@require_GET
def api_category_list_help(request):
    return API().get_category_list_help()


# stock
@csrf_exempt
@require_POST
def api_update_stock(request):
    return API().update_stock(request)
