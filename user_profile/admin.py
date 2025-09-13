from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import AuthAttempt, UserDayHistory
User = get_user_model()

class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name')
    search_fields = ('username', 'email', 'first_name', 'last_name')


admin.site.register(User, UserAdmin)
admin.site.register(AuthAttempt)
admin.site.register(UserDayHistory)
