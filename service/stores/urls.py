from django.urls import path

from . import views
from .helpers.api import API

api_full_path = API.get_api_full_path()

urlpatterns = [

    # store
    path('', views.StoreListView.as_view(), name='stores-list'),
    path('stores/', views.StoreListView.as_view(), name='stores-list'),
    path('stores/<int:pk>/detail/', views.view_store, name='stores-detail'),
    path('stores/add/', views.add_store, name='stores-add'),
    path('stores/<int:pk>/update/', views.update_store, name='stores-update'),
    path('stores/<int:pk>/delete/', views.StoreDeleteView.as_view(), name='stores-delete'),

    # brand
    path('brands/', views.GoodsBrandListView.as_view(), name='brands-list'),
    path('brands/<int:pk>/detail/', views.GoodsBrandDetailView.as_view(), name='brands-detail'),
    path('brands/add/', views.GoodsBrandCreateView.as_view(), name='brands-add'),
    path('brands/<int:pk>/update/', views.GoodsBrandUpdateView.as_view(), name='brands-update'),
    path('brands/<int:pk>/delete/', views.GoodsBrandDeleteView.as_view(), name='brands-delete'),

    # category
    path('categories/', views.get_categories_list, name='categories-list'),
    path('categories/add/', views.GoodsCategoryCreateView.as_view(), name='categories-add'),
    path('categories/<int:pk>/update/', views.GoodsCategoryUpdateView.as_view(), name='categories-update'),
    path('categories/<int:pk>/delete/', views.GoodsCategoryDeleteView.as_view(), name='categories-delete'),

    # good
    path('goods/', views.GoodListView.as_view(), name='goods-list'),
    path('goods/<int:pk>/detail/', views.GoodDetailView.as_view(), name='goods-detail'),
    path('goods/add/', views.GoodCreateView.as_view(), name='goods-add'),
    path('goods/<int:pk>/update/', views.GoodUpdateView.as_view(), name='goods-update'),
    path('goods/<int:pk>/delete/', views.GoodDeleteView.as_view(), name='goods-delete'),
    path('goods/batch-update-brand/', views.batch_update_brand, name='goods-batch-update-brand'),
    path('goods/batch-update-category/', views.batch_update_category, name='goods-batch-update-category'),
    path('goods/batch-upload/', views.batch_goods_upload, name='goods-batch-upload'),
    path('goods/batch-upload-success-file/<str:path>', views.batch_goods_upload_success_file,
         name='goods-batch-upload-success-file'),
    path('goods/export/', views.export_goods, name='goods-export'),
    # tmp utils for goods
    path('goods/generate/<int:count>', views.gen_goods, name='goods-generate'),
    path('goods/drop/', views.drop_goods, name='goods-drop'),

    # supplier
    path('suppliers/', views.SupplierListView.as_view(), name='suppliers-list'),
    path('suppliers/<int:pk>/detail/', views.SupplierDetailView.as_view(), name='suppliers-detail'),
    path('suppliers/add/', views.SupplierCreateView.as_view(), name='suppliers-add'),
    path('suppliers/<int:pk>/update/', views.SupplierUpdateView.as_view(), name='suppliers-update'),
    path('suppliers/<int:pk>/delete/', views.SupplierDeleteView.as_view(), name='suppliers-delete'),
    # tmp utils for suppliers
    path('suppliers/generate/<int:count>', views.gen_suppliers, name='suppliers-generate'),
    path('suppliers/drop/', views.drop_suppliers, name='suppliers-drop'),

    # warehouse
    path('warehouses/', views.WarehouseListView.as_view(), name='warehouses-list'),
    path('warehouses/<int:pk>/detail/', views.WarehouseDetailView.as_view(), name='warehouses-detail'),
    path('warehouses/add/', views.WarehouseCreateView.as_view(), name='warehouses-add'),
    path('warehouses/<int:pk>/update/', views.WarehouseUpdateView.as_view(), name='warehouses-update'),
    path('warehouses/<int:pk>/delete/', views.WarehouseDeleteView.as_view(), name='warehouses-delete'),

    # stock
    path('stock/', views.StockListView.as_view(), name='stock-list'),
    # tmp utils for stock
    path('stock/generate/', views.gen_stock, name='stock-generate'),
    path('stock/drop/', views.drop_stock, name='stock-drop'),

    # system
    path('systems/', views.SystemListView.as_view(), name='systems-list'),
    path('systems/<int:pk>/detail/', views.SystemDetailView.as_view(), name='systems-detail'),
    path('systems/add/', views.SystemCreateView.as_view(), name='systems-add'),
    path('systems/<int:pk>/update/', views.SystemUpdateView.as_view(), name='systems-update'),
    path('systems/<int:pk>/delete/', views.SystemDeleteView.as_view(), name='systems-delete'),

    # api
    # warehouse
    path(f'{api_full_path}/warehouses/', views.api_warehouse_list, name='api-warehouses-list'),
    path(f'{api_full_path}/warehouses/help/', views.api_warehouse_list_help, name='api-warehouses-list-help'),

    # category
    path(f'{api_full_path}/categories/', views.api_category_list, name='api-categories-list'),
    path(f'{api_full_path}/categories/help/', views.api_category_list_help, name='api-categories-list-help'),
]
