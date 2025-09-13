from django.contrib import admin
from .models import Subscription, UserSubscription
from csvexport.actions import csvexport


class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name', 'id')

class DecadeBornListFilter(admin.SimpleListFilter):
    title = 'Авто юзер?'

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'decade'

    def lookups(self, request, model_admin):
        return (
            ('auto', 'Авто Юзер'),
            ('no_auto', 'Норм Юзер'),
        )

    def queryset(self, request, queryset):

        if self.value() == 'auto':
            return queryset.filter(
                type=0
            )
        if self.value() == 'no_auto':
            return queryset.filter(
                type__gte=1
            )

class UserSubscriptionAdmin(admin.ModelAdmin):
    actions = [csvexport]
    csvexport_export_fields = [
        'type',
        'subscription.name',
        'valid_until',
        'user.email',
        'user.last_name',
        'user.first_name',
        'relational_field.field_a_on_related_model',
    ]
    search_fields = ('user__username', 'id', 'user__email')
    list_display = ('username', 'email', 'first_name', 'last_name', 'type', 'subscription', 'resubscribe_try')
    list_filter = [
        DecadeBornListFilter,
         "subscription", 
         "type"
    ]
    autocomplete_fields = ('trainer', 'user')
    @admin.display(ordering='user__username', description='username')
    def username(self, obj):
        return obj.user.username

    @admin.display(ordering='user__email', description='email')
    def email(self, obj):
        return obj.user.email

    @admin.display(ordering='user__first_name', description='first_name')
    def first_name(self, obj):
        return obj.user.first_name

    @admin.display(ordering='user__last_name', description='last_name')
    def last_name(self, obj):
        return obj.user.last_name


admin.site.register(Subscription, SubscriptionAdmin)
admin.site.register(UserSubscription, UserSubscriptionAdmin)
