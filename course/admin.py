from django.contrib import admin
# Register your models here.
from .models import Course, Lesson
from django_summernote.admin import SummernoteModelAdmin, SummernoteModelAdminMixin
from django.contrib.auth import get_user_model
from django.db.models import Q
User = get_user_model()
import modelclone
# Register your models here.
class LessonAdmin(SummernoteModelAdmin, modelclone.ClonableModelAdmin):
    model = Lesson
    summernote_fields = ['top_part', 'bot_part', 'inactive_text']
    list_display = ('name', 'course')

class CourseAdmin(SummernoteModelAdmin, modelclone.ClonableModelAdmin):
    summernote_fields = ['description']
    model = Course
    list_display = ('name', 'sub_name')
    autocomplete_fields = ('users',)
    def render_change_form(self, request, context, *args, **kwargs):
        kwargs['add'] = True
        return super(CourseAdmin, self).render_change_form(request, context, *args, **kwargs)

admin.site.register(Course, CourseAdmin)
admin.site.register(Lesson, LessonAdmin)