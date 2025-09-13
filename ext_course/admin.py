from django.contrib import admin
from .models import CourseReg, Course, CoursePromocode, AmoData
from csvexport.actions import csvexport
class PromocodeInline(admin.StackedInline):
    model = CoursePromocode
    extra = 0

class CourseAdmin(admin.ModelAdmin):
    inlines = [PromocodeInline]
    model = Course
    list_display = ['name', 'price']
    actions = [csvexport]

class CourseRegAdmin(admin.ModelAdmin):
    model = CourseReg
    list_display = ['name']
    actions = [csvexport]

admin.site.register(Course, CourseAdmin)
admin.site.register(AmoData)
admin.site.register(CourseReg, CourseRegAdmin)