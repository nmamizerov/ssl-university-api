from django.contrib import admin
from .models import Situation, SituationUser, userDecoding, SituationUserMark
# Register your models here.


admin.site.register(Situation)
admin.site.register(SituationUser)
admin.site.register(userDecoding)
admin.site.register(SituationUserMark)