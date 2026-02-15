from rest_framework import serializers
from .models import SalePurchase, CashBankTransaction


class SalePurchaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalePurchase
        fields = '__all__'


class CashBankTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CashBankTransaction
        fields = '__all__'