from django.contrib import admin
from .models import Company, CompanyEmails

class AnswerAdmin(admin.StackedInline):
    model = CompanyEmails
    extra = 0

class CompanyAdmin(admin.ModelAdmin):
    inlines = [AnswerAdmin]
    model = Company
    list_display = ['name']

admin.site.register(Company, CompanyAdmin)

# Register your models here.
