from django.db import models
from simulators.models import Simulator
from django.db.models import Max
from django.contrib.auth import get_user_model

User = get_user_model()

import logging
logger = logging.getLogger("django.server")

# Create your models here.
class TheoryChapter(models.Model):
    simulator = models.ForeignKey(Simulator, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    sequence_no = models.PositiveIntegerField(null=True)
    completed_by_user_set = models.ManyToManyField(User, blank=True, related_name='completed_theroies')

    @property
    def max_seq_no(self):
        seq_no = TheoryChapter.objects.filter(simulator=self.simulator).aggregate(Max("sequence_no"))['sequence_no__max']
        if seq_no:
            seq_no = seq_no + 1
        else:
            seq_no = 1
        return seq_no

    def __str__(self):
        return '{}. {}'.format(self.sequence_no, self.name)
    
    