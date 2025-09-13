from django.contrib import admin
# Register your models here.
from .models import botUser, Survey, Result, Category, Question, Answer, Survey_Question
from django_summernote.admin import SummernoteModelAdmin, SummernoteModelAdminMixin
# Register your models here.
class Survey_QuestionAdmin(admin.StackedInline):
    model = Survey_Question
    extra = 0
class AnswerAdmin(admin.StackedInline):
    model = Answer
    extra = 0

class QuestionAdmin(SummernoteModelAdmin):
    summernote_fields = '__all__'
    model = Question
    inlines = [AnswerAdmin]
    list_display = ('name', 'type')
class SurveyAdmin(SummernoteModelAdmin):
    summernote_fields = '__all__'
    model = Survey
    inlines = [Survey_QuestionAdmin]

admin.site.register(botUser)
admin.site.register(Survey, SurveyAdmin)
admin.site.register(Result)
admin.site.register(Category)
admin.site.register(Question, QuestionAdmin)