from django.contrib import admin
from .models import Payment, PromoCode
from csvexport.actions import csvexport

class PaymentAdmin(admin.ModelAdmin):
    readonly_fields = ["simulator", "subscription"]
    list_display = ('get_user_email', 'status', 'get_sub_id')
    search_fields = ('subscription__user__username', 'subscription__subscription__id')
    actions = [csvexport]
    csvexport_export_fields = [
        'sum',
        'id',
        
        'creation_time',
        'subscription.user.email',
        'subscription.user.last_name',
        'subscription.user.first_name',
    ]
    list_filter = [
         "status"
    ]
    @admin.display(description='Email', ordering='subscription__user__email')
    def get_user_email(self, obj):
        if obj.subscription is not None:
            return obj.subscription.user.email
        else:
            return "-"
    @admin.display(description='ID', ordering='subscription__subscription__id')
    def get_sub_id(self, obj):
        if obj.subscription is not None and obj.subscription.subscription is not None:
            return obj.subscription.subscription.id
        else:
            return "-"
admin.site.register(PromoCode)
admin.site.register(Payment, PaymentAdmin)
