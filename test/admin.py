from django.contrib import admin
from .models import Category, Context, Skill, CategorySkill, Result
from django_summernote.admin import SummernoteModelAdmin, SummernoteModelAdminMixin
# Register your models here.

class CategorySkillAdmin(SummernoteModelAdminMixin, admin.StackedInline):
    model = CategorySkill
    summernote_fields = '__all__'

class CategoryAdmin(SummernoteModelAdmin):
    summernote_fields = '__all__'
    model = Category
    inlines = [CategorySkillAdmin]

class SkillAdmin(SummernoteModelAdmin):
    summernote_fields = '__all__'
    model = Skill
    inlines = [CategorySkillAdmin]

class ContextAdmin(SummernoteModelAdmin):
    summernote_fields = '__all__'
    model = Context

admin.site.register(Category, CategoryAdmin)
admin.site.register(Context, ContextAdmin)
admin.site.register(Skill, SkillAdmin)
admin.site.register(CategorySkill)
admin.site.register(Result)
