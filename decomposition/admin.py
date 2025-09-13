from django.contrib import admin
from .models import FeedbackSituation, FeedbackSituationUser, FeedbackSituationUserMark
# Register your models here.
class FeedbackSituationUserAdmin(admin.ModelAdmin):
    readonly_fields = ('user',)

admin.site.register(FeedbackSituation)
admin.site.register(FeedbackSituationUser, FeedbackSituationUserAdmin)
admin.site.register(FeedbackSituationUserMark)