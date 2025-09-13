from django.db import models
from django.contrib.postgres.fields import JSONField
from django.core.serializers.json import DjangoJSONEncoder
import random
import string

def rand_slug():
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(8))

class Category(models.Model):
    name = models.CharField(max_length=255, verbose_name='Название')
    icon = models.FileField(upload_to='tests', blank=True, null=True, verbose_name='Иконка')
    description = models.TextField()
    img = models.ImageField(upload_to='tests', blank=True, null=True, verbose_name='Картинка')
    slug = models.CharField(max_length=255, verbose_name='slug')
    def __str__(self):
        return self.name

class Context(models.Model):
    name = models.CharField(max_length=255, verbose_name='Название')
    description = models.TextField()
    slug = models.CharField(max_length=255, verbose_name='slug', blank=True)
    def __str__(self):
        return self.name

class Skill(models.Model):
    name = models.CharField(max_length=255, verbose_name='Название')
    books = models.TextField(blank=True)
    simulators = models.TextField(blank=True)
    excercises = models.TextField(blank=True)
    more = models.TextField(blank=True)
    categories = models.ManyToManyField(Category, through='CategorySkill')    
    slug = models.CharField(max_length=255, verbose_name='slug')
    def __str__(self):
        return self.name

class CategorySkill(models.Model):
    category = models.ForeignKey('Category', on_delete=models.CASCADE, null=True, blank=True)
    skill = models.ForeignKey('Skill', on_delete=models.CASCADE, null=True, blank=True)
    description = models.TextField()
    img = models.ImageField(upload_to='tests', blank=True, null=True, verbose_name='Картинка')
    def __str__(self):
        return f'категория: {self.category.name}, Навык: {self.skill.name}'

class Result(models.Model): 
    name = models.CharField(max_length=255, verbose_name='Имя тестируемого')
    tester = models.CharField(max_length=255, verbose_name='Тестирующий')
    version = models.IntegerField(default = 1)
    data = JSONField(null=True, blank=True, encoder=DjangoJSONEncoder)
    slug = models.CharField(max_length=8, unique=True, default=rand_slug)
    def __str__(self):
        return self.name

