from rest_framework import viewsets
from .models import SalePurchase, CashBankTransaction
from .serializers import SalePurchaseSerializer, CashBankTransactionSerializer


class SalePurchaseViewSet(viewsets.ModelViewSet):
    queryset = SalePurchase.objects.all()
    serializer_class = SalePurchaseSerializer


class CashBankTransactionViewSet(viewsets.ModelViewSet):
    queryset = CashBankTransaction.objects.all()
    serializer_class = CashBankTransactionSerializer