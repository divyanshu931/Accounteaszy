from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SalePurchaseViewSet, CashBankTransactionViewSet

router = DefaultRouter()
router.register(r'sale-purchase', SalePurchaseViewSet)
router.register(r'cash-bank', CashBankTransactionViewSet)

urlpatterns = [
    path('', include(router.urls)),
]