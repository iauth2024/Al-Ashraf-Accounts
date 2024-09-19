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
