from django.db import models


class Recommendation(models.Model):
    group = models.ForeignKey('simulator_groups.SimulatorGroup', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    text = models.TextField(blank=True, null=True)
    link = models.CharField(max_length=255, blank=True, null=True)
    image = models.ImageField(upload_to='recommendations_images', blank=True, null=True)
    lessons = models.ManyToManyField('lessons.Lesson', blank=True)
    def __str__(self):
        return f'{self.title}: {self.link}'
