from django.contrib import admin
from .models import CronLog


class CronLogAdmin(admin.ModelAdmin):
    readonly_fields = ["user"]
admin.site.register(CronLog, CronLogAdmin)
