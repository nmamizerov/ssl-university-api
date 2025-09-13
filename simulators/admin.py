from django.contrib import admin
from .models import Simulator, SimulatorUser
from csvexport.actions import csvexport

class SimulatorAdmin(admin.ModelAdmin):
    raedonly_fields = ['completed_by_user_set']

class SimulatorUserAdmin(admin.ModelAdmin):
    actions = [csvexport]
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name', 'simulator__group__id')
    list_display = ('username', 'email', 'first_name', 'last_name', 'group')
    
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

    @admin.display(ordering='simulator__group', description='group')
    def group(self, obj):
        return obj.simulator.group


admin.site.register(Simulator, SimulatorAdmin)
admin.site.register(SimulatorUser, SimulatorUserAdmin)
