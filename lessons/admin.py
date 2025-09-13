from django.contrib import admin
from .models import Lesson, UserLessonProgress


class LessonAdmin(admin.ModelAdmin):
    search_fields = ('name', 'slug', 'id')




admin.site.register(Lesson, LessonAdmin)

class UserLessonProgressAdmin(admin.ModelAdmin):
    readonly_fields = ('user','lesson')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name', 'lesson__name')
    list_display = ('username', 'email', 'first_name', 'last_name', 'lesson', 'completed')

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

    @admin.display(ordering='simulator__group', description='lesson')
    def group(self, obj):
        return obj.simulator.group

admin.site.register(UserLessonProgress, UserLessonProgressAdmin)
