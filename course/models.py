from django.db import models
from django.contrib.auth import get_user_model
import random
import string
from sortedm2m.fields import SortedManyToManyField
User = get_user_model()

def rand_slug():
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(6))
# Create your models here.




class Course(models.Model):
    name = models.CharField(max_length=255, verbose_name='Название')
    sub_name = models.CharField(max_length=255, verbose_name='название серым (например, обозначить поток + подписку)')
    show_front = models.BooleanField(default=False)
    link = models.TextField(blank = True, null = True)
    description = models.TextField(blank = True, null = True)
    image = models.ImageField(upload_to='course', blank=True, null=True)
    slug = models.CharField(max_length=255, verbose_name='slug', unique=True)
    users = models.ManyToManyField(User, blank=True, null=True)
    company = models.ManyToManyField("company.Company", verbose_name="Компания", null=True, blank=True)
    current = models.IntegerField(default=1)
    is_base = models.BooleanField(default=False)
    is_next = models.BooleanField(default=False)
    badge_text = models.TextField(blank = True, null = True)
    def __str__(self):
        return f"{self.name} {self.sub_name}"

class Lesson(models.Model):
    name = models.CharField(max_length=255, verbose_name='Название')
    course = models.ForeignKey('Course', on_delete=models.CASCADE, null=True, blank=True)
    order = models.IntegerField(default=0)
    link = models.TextField()
    active = models.BooleanField(default=False, verbose_name="Активно, если нет, то будет стоять ссылка на занятие")
    lessons = SortedManyToManyField("lessons.Lesson", related_name="lessons_Course")
    link = models.TextField(blank = True, null = True)
    inactive_text = models.TextField(verbose_name='Текст, если ссылка на занятие', blank=True )
    top_part = models.TextField(verbose_name='Обычно, место для видеозаписи', blank=True )
    bot_part = models.TextField(verbose_name='Обычно, место для домашних работ и прочей информации', blank=True)
    def __str__(self):
        return f"{self.name}"