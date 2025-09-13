from django.db import models


class Tag(models.Model):
    group = models.ForeignKey('simulator_groups.SimulatorGroup', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    lessons = models.ManyToManyField('lessons.Lesson', blank=True)
    is_show = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.name} ({self.id})'
