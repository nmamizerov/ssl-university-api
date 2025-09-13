from django.contrib import admin

# Register your models here.
from .models import SimulatorGroup

class SimulatorGroupAdmin(admin.ModelAdmin):
    readonly_fields = ('owner',)
    model = SimulatorGroup


admin.site.register(SimulatorGroup, SimulatorGroupAdmin)