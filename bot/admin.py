from django.contrib import admin
from .models import tgUser, tgSend,AITg
# Register your models here.
admin.site.register(tgUser)
admin.site.register(tgSend)
admin.site.register(AITg)