from django.db import models

# Create your models here.
class Company(models.Model):
    name = models.CharField(max_length=255, verbose_name='Название')
    logo = models.ImageField(upload_to='company', blank=True, null=True)
    slug = models.CharField(max_length=30, verbose_name='slug', unique=True)
    show_default_nav = models.BooleanField(default=True)
    show_default_courses = models.BooleanField(default=True)
    custom_simulator = models.ForeignKey('simulators.Simulator', null=True, blank=True, on_delete=models.SET_NULL)
    def __str__(self):
        return f"{self.name}"

class CompanyEmails(models.Model): 
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    email = models.CharField(max_length=255, verbose_name='email')
    def __str__(self):
        return f"{self.email}"