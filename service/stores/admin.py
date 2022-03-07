from django.contrib import admin
from .models import StoreStatus
from .models import StoreType
from .models import Marketplace
from .models import Store
from .models import MarketplaceProperty
from .models import StoreProperty
from .models import GoodsBrand
from .models import GoodsCategory
from .models import Good

from .models import WarehouseType
from .models import Supplier
from .models import Warehouse

from .models import Stock
from .models import System
from .models import StockSetting
from .models import StoreWarehouse

from .models import Log
from .models import LogRow

from .models import Job
from .models import UserJob
from .models import JobState
from .models import UserJobLog

from .models import OrderStatus
from .models import OrderMarketplaceStatus
from .models import Order
from .models import OrderItem
from .models import OrderShipment

admin.site.register(StoreStatus)
admin.site.register(StoreType)
admin.site.register(Marketplace)
admin.site.register(Store)
admin.site.register(StoreWarehouse)
admin.site.register(MarketplaceProperty)
admin.site.register(StoreProperty)

admin.site.register(GoodsBrand)
admin.site.register(GoodsCategory)
admin.site.register(Good)

admin.site.register(WarehouseType)
admin.site.register(Supplier)
admin.site.register(Warehouse)

admin.site.register(Stock)
admin.site.register(System)
admin.site.register(StockSetting)

admin.site.register(Log)
admin.site.register(LogRow)

admin.site.register(Job)
admin.site.register(JobState)
admin.site.register(UserJob)
admin.site.register(UserJobLog)

admin.site.register(OrderStatus)
admin.site.register(OrderMarketplaceStatus)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(OrderShipment)
