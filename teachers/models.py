from django.db import models

class Teacher(models.Model):
    name = models.CharField(max_length=255, verbose_name='Фамилия Имя')
    img = models.ImageField(upload_to='teachers', blank=True, null=True)
    tag = models.ManyToManyField('Tags', blank=True)
    heading = models.TextField(max_length=200, null=True, blank=True, verbose_name='Жирное описание')
    small_description = models.TextField(max_length=200, null=True, blank=True, verbose_name='Маленькое описание (не более 200 символов без html)')
    from_teacher = models.TextField(null=True, blank=True, verbose_name='Описание словами учителя')
    education = models.TextField(null=True, blank=True, verbose_name='Образование')
    results = models.TextField(null=True, blank=True, verbose_name='Достижения')
    price = models.IntegerField(null=True, blank=True)
    slug = models.CharField(max_length=20, null=True, blank=True)
    order = models.IntegerField(verbose_name='Порядок вывода. Чем больше, тем первее')
    def __str__(self):
        return self.name

class Tags(models.Model):
    name = models.CharField(max_length=255, verbose_name='Название')
    def __str__(self):
        return self.name
# Create your models here.
