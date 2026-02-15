from django.contrib import admin
from django.urls import path, reverse
from django.template.response import TemplateResponse
from django.utils.html import format_html
from django.shortcuts import get_object_or_404
from decimal import Decimal
from django.http import HttpResponse
from django.db.models import Sum

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import pagesizes

from .models import (
    Account,
    Party,
    Inventory,
    Sale,
    Purchase,
    ReceiveMoney,
    PayMoney,
    SalePurchase,
    CashBankTransaction,
)

# =====================================================
# ADMIN BRANDING
# =====================================================

admin.site.site_header = "Bhavikha Plastic Pvt Ltd"
admin.site.site_title = "Bhavikha Plastic Admin"
admin.site.index_title = "Bhavikha Plastic Accounts Panel"


# =====================================================
# ACCOUNT ADMIN
# =====================================================

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'account_type', 'balance', 'view_ledger')
    readonly_fields = ('balance', 'created_at')

    def view_ledger(self, obj):
        url = reverse("admin:account-ledger", args=[obj.pk])
        return format_html('<a class="button" href="{}">View Ledger</a>', url)

    view_ledger.short_description = "Ledger"

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "<int:account_id>/account-ledger/",
                self.admin_site.admin_view(self.account_ledger_view),
                name="account-ledger",
            ),
        ]
        return custom + urls

    def account_ledger_view(self, request, account_id):
        account = get_object_or_404(Account, pk=account_id)

        sales = SalePurchase.objects.filter(
            account=account,
            payment_mode="cash"
        )

        cash_txns = CashBankTransaction.objects.filter(
            account=account
        )

        combined = []

        for s in sales:
            combined.append({
                "date": s.date,
                "type": s.purpose.upper(),
                "party": s.party.name,
                "amount": s.amount
            })

        for c in cash_txns:
            combined.append({
                "date": c.date,
                "type": c.transaction_type.upper(),
                "party": c.party.name,
                "amount": c.amount
            })

        combined.sort(key=lambda x: x["date"])

        balance = account.opening_balance or Decimal("0")

        ledger = []
        for entry in combined:

            if entry["type"] in ["SALE", "RECEIVE"]:
                balance += entry["amount"]
                credit = entry["amount"]
                debit = Decimal("0")
            else:
                balance -= entry["amount"]
                debit = entry["amount"]
                credit = Decimal("0")

            ledger.append({
                "date": entry["date"],
                "type": entry["type"],
                "party": entry["party"],
                "debit": debit,
                "credit": credit,
                "balance": balance
            })

        return TemplateResponse(
            request,
            "account_ledger.html",
            {
                **self.admin_site.each_context(request),
                "account": account,
                "ledger": ledger,
            },
        )


# =====================================================
# PARTY ADMIN WITH LEDGER
# =====================================================

@admin.register(Party)
class PartyAdmin(admin.ModelAdmin):
    list_display = ('name', 'party_type', 'credit_balance', 'view_ledger')
    list_filter = ('party_type',)

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ('opening_balance', 'credit_balance')
        return ('credit_balance',)

    def view_ledger(self, obj):
        url = reverse("admin:party-ledger", args=[obj.pk])
        return format_html('<a class="button" href="{}">View Ledger</a>', url)

    view_ledger.short_description = "Ledger"

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "<int:party_id>/ledger/",
                self.admin_site.admin_view(self.party_ledger_view),
                name="party-ledger",
            ),
        ]
        return custom + urls

    def party_ledger_view(self, request, party_id):
        party = get_object_or_404(Party, pk=party_id)

        sales = SalePurchase.objects.filter(party=party)
        cash = CashBankTransaction.objects.filter(party=party)

        combined = []

        for s in sales:
            combined.append({
                "date": s.date,
                "type": s.purpose.upper(),
                "mode": s.payment_mode.upper(),
                "product": s.inventory.name,
                "quantity": s.quantity,
                "rate": s.price_per_unit,
                "amount": s.amount
            })

        for c in cash:
            combined.append({
                "date": c.date,
                "type": c.transaction_type.upper(),
                "mode": "CASH",
                "product": "-",
                "quantity": "",
                "rate": "",
                "amount": c.amount
            })

        combined.sort(key=lambda x: x["date"])

        balance = party.opening_balance or Decimal("0")
        ledger = []

        for entry in combined:

            # Only credit transactions affect receivable
            if entry["type"] == "SALE" and entry["mode"] == "CREDIT":
                balance += entry["amount"]

            elif entry["type"] == "PURCHASE" and entry["mode"] == "CREDIT":
                balance -= entry["amount"]

            elif entry["type"] == "RECEIVE":
                balance -= entry["amount"]

            elif entry["type"] == "PAY":
                balance += entry["amount"]

            ledger.append({
                **entry,
                "balance": balance
            })

        return TemplateResponse(
            request,
            "party_ledger.html",
            {
                **self.admin_site.each_context(request),
                "party": party,
                "ledger": ledger,
            },
        )
# =====================================================
# INVENTORY ADMIN WITH STOCK LEDGER (FIXED VERSION)
# =====================================================

@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'quantity',   # ✅ This is real current stock
        'unit',
        'default_price',
        'view_stock_ledger'
    )

    # -------------------------------
    # LEDGER BUTTON
    # -------------------------------
    def view_stock_ledger(self, obj):
        url = reverse("admin:inventory-stock-ledger", args=[obj.pk])
        return format_html(
            '<a class="button" href="{}">View Stock Ledger</a>',
            url
        )

    view_stock_ledger.short_description = "Stock Ledger"

    # -------------------------------
    # CUSTOM URL
    # -------------------------------
    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "<int:product_id>/stock-ledger/",
                self.admin_site.admin_view(self.stock_ledger_view),
                name="inventory-stock-ledger",
            ),
        ]
        return custom + urls

    # -------------------------------
    # STOCK LEDGER VIEW (CORRECT)
    # -------------------------------
    def stock_ledger_view(self, request, product_id):
        product = get_object_or_404(Inventory, pk=product_id)

        transactions = SalePurchase.objects.filter(
            inventory=product
        ).order_by("-date")  # 🔥 reverse order

        running_stock = product.quantity or Decimal("0")  # ✅ start from REAL stock

        ledger = []

        for txn in transactions:

            if txn.purpose == "sale":
                qty_in = Decimal("0")
                qty_out = txn.quantity
                stock_before = running_stock + txn.quantity

            else:  # purchase
                qty_in = txn.quantity
                qty_out = Decimal("0")
                stock_before = running_stock - txn.quantity

            ledger.append({
                "date": txn.date,
                "type": txn.purpose.upper(),
                "party": txn.party.name,
                "mode": txn.payment_mode.upper(),
                "qty_in": qty_in,
                "qty_out": qty_out,
                "rate": txn.price_per_unit,
                "stock": running_stock,          # stock after transaction
                "stock_before": stock_before     # optional
            })

            running_stock = stock_before

        ledger.reverse()  # show oldest first

        return TemplateResponse(
            request,
            "inventory_stock_ledger.html",
            {
                **self.admin_site.each_context(request),
                "product": product,
                "ledger": ledger,
                "calculated_stock": product.quantity,  # ✅ real stock
            },
        )
# =====================================================
# SALES / PURCHASE / CASH PROXY ADMINS
# =====================================================

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('date', 'party', 'inventory', 'quantity', 'amount')
    readonly_fields = ('date',)

    def get_queryset(self, request):
        return super().get_queryset(request).filter(purpose='sale')

    def save_model(self, request, obj, form, change):
        obj.purpose = 'sale'
        super().save_model(request, obj, form, change)


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('date', 'party', 'inventory', 'quantity', 'amount')
    readonly_fields = ('date',)

    def get_queryset(self, request):
        return super().get_queryset(request).filter(purpose='purchase')

    def save_model(self, request, obj, form, change):
        obj.purpose = 'purchase'
        super().save_model(request, obj, form, change)


@admin.register(ReceiveMoney)
class ReceiveMoneyAdmin(admin.ModelAdmin):
    list_display = ('date', 'party', 'account', 'amount')
    readonly_fields = ('date',)

    def get_queryset(self, request):
        return super().get_queryset(request).filter(transaction_type='receive')

    def save_model(self, request, obj, form, change):
        obj.transaction_type = 'receive'
        super().save_model(request, obj, form, change)


@admin.register(PayMoney)
class PayMoneyAdmin(admin.ModelAdmin):
    list_display = ('date', 'party', 'account', 'amount')
    readonly_fields = ('date',)

    def get_queryset(self, request):
        return super().get_queryset(request).filter(transaction_type='pay')

    def save_model(self, request, obj, form, change):
        obj.transaction_type = 'pay'
        super().save_model(request, obj, form, change)