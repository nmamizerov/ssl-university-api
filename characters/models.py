from django.db import models
from lessons.models import Lesson
from simulators.models import Simulator
from user_profile.models import User
from django.contrib.postgres.fields import JSONField
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Max

import logging
logger = logging.getLogger("django.server")

# Create your models here.
class Character(models.Model):
    simulator = models.ForeignKey(Simulator, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200)
    default_role = models.CharField(max_length=200)
    is_user = models.BooleanField(default=False)
    male = models.BooleanField(default=True)
    avatar = models.ImageField( upload_to='character_avatars', null=True, blank=True)

    def __str__(self):
        return '({}) {} {}'.format(self.id, self.first_name, self.last_name)
    
    
    