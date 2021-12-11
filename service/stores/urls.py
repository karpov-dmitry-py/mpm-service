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
    path('goods/drop_test_goods/', views.drop_test_goods, name='drop-test-goods'),
    path('goods/drop_all_goods/', views.drop_all_goods, name='drop-all-goods'),

    # internal api
    path('goods/user', views.get_user_goods, name='user-goods'),

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

    # stock settings
    path('settings/stock/warehouse/<int:wh_pk>/list/', views.StockSettingListView.as_view(),
         name='stock-settings-list'),
    path('settings/stock/warehouse/<int:wh_pk>/add/', views.StockSettingCreateView.as_view(),
         name='stock-settings-add'),
    path('settings/stock/<int:pk>/update/', views.StockSettingUpdateView.as_view(), name='stock-settings-update'),
    path('settings/stock/<int:pk>/delete/', views.StockSettingDeleteView.as_view(), name='stock-settings-delete'),
    path('settings/stock/batch-delete/', views.stock_settings_batch_delete, name='stock-settings-batch-delete'),

    # store warehouses
    path('stores/<int:store_pk>/warehouses/', views.StoreWarehouseListView.as_view(), name='store-warehouses-list'),
    path('stores/<int:store_pk>/warehouses/add', views.StoreWarehouseCreateView.as_view(), name='store-warehouses-add'),
    path('stores/warehouses/<int:pk>/detail/', views.StoreWarehouseDetailView.as_view(),
         name='store-warehouses-detail'),
    path('stores/warehouses/<int:pk>/update/', views.StoreWarehouseUpdateView.as_view(),
         name='store-warehouses-update'),
    path('stores/warehouses/<int:pk>/delete/', views.StoreWarehouseDeleteView.as_view(),
         name='store-warehouses-delete'),

    # update stock in marketplace via api
    path('stores/warehouses/<int:pk>/stock/update', views.store_wh_update_stock,
         name='store-warehouses-out-api-stock-update'),

    # logs
    path('logs/', views.LogListView.as_view(), name='logs-list'),
    path('logs/<int:pk>/detail/', views.LogDetailView.as_view(), name='logs-detail'),
    path('logs/<int:pk>/export/', views.log_export, name='logs-export'),


    # user job
    path('jobs/', views.UserJobListView.as_view(), name='user-jobs-list'),
    path('jobs/add/', views.UserJobCreateView.as_view(), name='user-jobs-add'),
    path('jobs/<int:pk>/detail/', views.UserJobDetailView.as_view(), name='user-jobs-detail'),
    path('jobs/<int:pk>/update/', views.UserJobUpdateView.as_view(), name='user-jobs-update'),
    path('jobs/<int:pk>/run/', views.run_user_job, name='user-jobs-run'),

    # cron jobs
    path('jobs/cron/list', views.get_cron_jobs, name='cron-jobs-list'),
    path('jobs/cron/delete', views.disable_user_jobs, name='cron-jobs-delete-all'),

    # API
    # help page
    path(f'{api_full_path}/help/', views.api_help, name='api-help'),

    # warehouse
    path(f'{api_full_path}/warehouses/', views.api_warehouse_list, name='api-warehouses-list'),
    # path(f'{api_full_path}/warehouses/help/', views.api_warehouse_list_help, name='api-warehouses-list-help'),

    # category
    path(f'{api_full_path}/categories/', views.api_category_list, name='api-categories-list'),
    # path(f'{api_full_path}/categories/help/', views.api_category_list_help, name='api-categories-list-help'),

    # stock
    path(f'{api_full_path}/stock/', views.api_update_stock, name='api-update-stock'),

    # yandex
    path(f'{views.get_stocks_by_store_api_url()}', views.api_yandex_update_stock, name='api-yandex-update-stock'),

    # misc
    path('misc/suppliers/offers/check', views.process_categories_choice, name='suppliers-offers-check'),

]
