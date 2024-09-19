from django.contrib import admin
from .models import UserActivityLog, Voucher, HeadOfAccount, Receipt

# Register models
admin.site.register(Receipt)
admin.site.register(HeadOfAccount)

@admin.register(Voucher)
class VoucherAdmin(admin.ModelAdmin):
    list_display = ['voucher_no', 'paid_to', 'amount', 'status', 'created_date', 'created_by']
    list_filter = ['status', 'created_date']
    search_fields = ['voucher_no', 'paid_to', 'created_by__username']

    fieldsets = (
        ('Voucher Information', {
            'fields': ('voucher_no', 'paid_to', 'on_account_of', 'head_of_account', 'mode_of_payment',
                       'transaction_id', 'amount', 'amount_in_words', 'voucher_date', 'received_by')
        }),
        ('Approval Information', {
            'fields': ('status', 'approved_by', 'rejection_reason')
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:  # Only set created_by on creation, not on updates
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
@admin.register(UserActivityLog)
class UserActivityLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'timestamp', 'screen_time', 'work_time')
    list_filter = ('user', 'timestamp')
    search_fields = ('user__username',)

from django.contrib import admin
from .models import Contra, Balance
from django.contrib.auth.models import User

class ContraAdmin(admin.ModelAdmin):
    list_display = ('contra_no', 'amount', 'date', 'contra_type', 'performed_by')
    list_filter = ('contra_type', 'date', 'performed_by')
    search_fields = ('contra_no', 'amount', 'date', 'contra_type', 'performed_by__username')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('performed_by')

    def save_model(self, request, obj, form, change):
        if not change:  # This is a new instance
            super().save_model(request, obj, form, change)
            obj.reverse_contra_transaction()
        else:
            super().save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        obj.reverse_contra_transaction()
        super().delete_model(request, obj)

class BalanceAdmin(admin.ModelAdmin):
    list_display = ('cash_balance', 'non_cash_balance')
    readonly_fields = ('cash_balance', 'non_cash_balance')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.none()  # To ensure only one Balance record is shown

    def has_change_permission(self, request, obj=None):
        return False  # Prevent modification through the admin interface

admin.site.register(Contra, ContraAdmin)
admin.site.register(Balance, BalanceAdmin)
