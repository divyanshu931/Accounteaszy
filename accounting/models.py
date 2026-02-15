# accounting/models.py

from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.db import transaction as db_transaction
from django.core.exceptions import ValidationError


# =====================================================
# ACCOUNT MODEL (Cash / Bank)
# =====================================================

class Account(models.Model):

    ACCOUNT_TYPES = (
        ('cash', 'Cash'),
        ('bank', 'Bank'),
    )

    name = models.CharField(
        max_length=100,
        unique=True
    )

    account_type = models.CharField(
        max_length=10,
        choices=ACCOUNT_TYPES
    )

    opening_balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        editable=False
    )

    created_at = models.DateTimeField(auto_now_add=True)

    # -------------------------------------------------

    def save(self, *args, **kwargs):

        # On first creation → set balance = opening balance
        if not self.pk:
            self.balance = self.opening_balance

        super().save(*args, **kwargs)

    # -------------------------------------------------

    def __str__(self):
        return f"{self.name} ({self.account_type}) - Balance: {self.balance}"


# =====================================================
# PARTY MODEL (Customer / Supplier)
# =====================================================

# =====================================================
# PARTY MODEL (Customer / Supplier)
# =====================================================

class Party(models.Model):

    PARTY_TYPES = (
        ('customer', 'Customer'),
        ('supplier', 'Supplier'),
    )

    name = models.CharField(max_length=255)
    party_type = models.CharField(max_length=20, choices=PARTY_TYPES)
    phone = models.CharField(max_length=20, blank=True)

    # Opening balance at time of creation
    opening_balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Customer: positive means they owe us. Supplier: negative means we owe them."
    )

    # Running balance (auto updated by transactions)
    credit_balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        editable=False
    )

    created_at = models.DateTimeField(auto_now_add=True)

    # -------------------------------------------------

    def save(self, *args, **kwargs):

        # On first creation → set credit_balance = opening_balance
        if not self.pk:
            self.credit_balance = self.opening_balance

        super().save(*args, **kwargs)

    # -------------------------------------------------

    def __str__(self):
        return f"{self.name} ({self.party_type}) - Balance: {self.credit_balance}"

# =====================================================

# INVENTORY MODEL
# =====================================================

class Inventory(models.Model):

    UNIT_CHOICES = (
        ('kg', 'Kilogram'),
        ('pcs', 'Pieces'),
    )

    name = models.CharField(max_length=255, unique=True)

    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    unit = models.CharField(
        max_length=10,
        choices=UNIT_CHOICES,
        default='kg'
    )

    default_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    def __str__(self):
        return f"{self.name} ({self.quantity} {self.unit})"


# =====================================================
# SALE / PURCHASE MODEL (Main Table)
# =====================================================

class SalePurchase(models.Model):

    PURPOSE = (
        ('sale', 'Sale'),
        ('purchase', 'Purchase'),
    )

    PAYMENT_MODE = (
        ('cash', 'Cash'),
        ('credit', 'Credit'),
    )

    purpose = models.CharField(
        max_length=10,
        choices=PURPOSE,
        editable=False  # will be auto-set from admin
    )

    payment_mode = models.CharField(max_length=10, choices=PAYMENT_MODE)

    party = models.ForeignKey(Party, on_delete=models.PROTECT)
    inventory = models.ForeignKey(Inventory, on_delete=models.PROTECT)

    account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        help_text="Required only for cash transactions"
    )

    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )

    price_per_unit = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        editable=False
    )

    date = models.DateTimeField(default=timezone.now)

    # -------------------------------------------------

    def clean(self):

        if self.payment_mode == 'cash' and not self.account:
            raise ValidationError("Cash transaction requires account.")

        if self.payment_mode == 'credit' and self.account:
            raise ValidationError("Credit transaction should not have account.")

    # -------------------------------------------------

    def save(self, *args, **kwargs):

        with db_transaction.atomic():

            self.full_clean()

            if self.pk:
                raise ValidationError("Editing not allowed.")

            self.amount = self.quantity * self.price_per_unit

            # ================= SALE =================
            if self.purpose == "sale":

                if self.party.party_type != "customer":
                    raise ValidationError("Sale must be to customer.")

                if self.inventory.quantity < self.quantity:
                    raise ValidationError("Not enough stock.")

                self.inventory.quantity -= self.quantity

                if self.payment_mode == "cash":
                    self.account.balance += self.amount
                    self.account.save()
                else:
                    self.party.credit_balance += self.amount
                    self.party.save()

            # ================= PURCHASE =================
            elif self.purpose == "purchase":

                if self.party.party_type != "supplier":
                    raise ValidationError("Purchase must be from supplier.")

                self.inventory.quantity += self.quantity

                if self.payment_mode == "cash":
                    self.account.balance -= self.amount
                    self.account.save()
                else:
                    self.party.credit_balance -= self.amount
                    self.party.save()

            self.inventory.save()

            super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.purpose.upper()} - {self.party.name} - {self.amount}"


# =====================================================
# PROXY MODELS (UI Separation Only)
# =====================================================

class Sale(SalePurchase):
    class Meta:
        proxy = True
        verbose_name = "Sale"
        verbose_name_plural = "Sales"


class Purchase(SalePurchase):
    class Meta:
        proxy = True
        verbose_name = "Purchase"
        verbose_name_plural = "Purchases"
# =====================================================
# CASH / BANK TRANSACTION MODEL (Main Table)
# =====================================================

class CashBankTransaction(models.Model):

    TRANSACTION_TYPE = (
        ('receive', 'Receive'),
        ('pay', 'Pay'),
    )

    transaction_type = models.CharField(
        max_length=10,
        choices=TRANSACTION_TYPE,
        editable=False  # will be auto-set
    )

    party = models.ForeignKey(Party, on_delete=models.PROTECT)
    account = models.ForeignKey(Account, on_delete=models.PROTECT)

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )

    date = models.DateTimeField(default=timezone.now)

    # --------------------------------------------

    def save(self, *args, **kwargs):

        with db_transaction.atomic():

            if self.pk:
                raise ValidationError("Editing not allowed.")

            # ===== RECEIVE MONEY =====
            if self.transaction_type == "receive":

                if self.party.party_type != "customer":
                    raise ValidationError("Can only receive from customer.")

                self.account.balance += self.amount
                self.party.credit_balance -= self.amount

            # ===== PAY MONEY =====
            elif self.transaction_type == "pay":

                if self.party.party_type != "supplier":
                    raise ValidationError("Can only pay to supplier.")

                self.account.balance -= self.amount
                self.party.credit_balance += self.amount

            self.account.save()
            self.party.save()

            super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.transaction_type.upper()} - {self.party.name} - {self.amount}"

# =====================================================
# PROXY MODELS FOR CLEAN UI
# =====================================================

class ReceiveMoney(CashBankTransaction):
    class Meta:
        proxy = True
        verbose_name = "Receive Money"
        verbose_name_plural = "Receive Money"


class PayMoney(CashBankTransaction):
    class Meta:
        proxy = True
        verbose_name = "Pay Money"
        verbose_name_plural = "Pay Money"    