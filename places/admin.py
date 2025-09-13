from django.contrib import admin
from .models import Place, PlaceUser


class PlaceUserAdmin(admin.ModelAdmin):
    search_fields = ['place__id', 'user__email', 'place__page__name']
    list_display = ('place_id', 'email', 'page')
    readonly_fields = ('place', 'user', 'commented_by_user_set')
    @admin.display(ordering='place_id', description='place_id')
    def place_id(self, obj):
        return obj.place.id

    @admin.display(ordering='user__email', description='email')
    def email(self, obj):
        return obj.user.email

    @admin.display(ordering='place__page__name', description='page')
    def page(self, obj):
        return obj.place.page.name


class PlaceAdmin(admin.ModelAdmin):
    search_fields = ['id', 'text', 'title']


admin.site.register(Place, PlaceAdmin)
admin.site.register(PlaceUser, PlaceUserAdmin)
