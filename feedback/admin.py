from django.contrib import admin
from .models import FeedbackSituation, FeedbackSituationUser, FeedbackSituationUserMark
# Register your models here.
class FeedbackSituationUserAdmin(admin.ModelAdmin):
    readonly_fields = ('user',)
    list_display = ('pk','user', 'situation' )
class FeedbackSituationUserMarkAdmin(admin.ModelAdmin):
    list_display = ('pk', 'comment', )


admin.site.register(FeedbackSituation)
admin.site.register(FeedbackSituationUser, FeedbackSituationUserAdmin)
admin.site.register(FeedbackSituationUserMark, FeedbackSituationUserMarkAdmin)