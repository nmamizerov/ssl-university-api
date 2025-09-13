from django.db import models


class Banner(models.Model):
    group = models.ForeignKey('simulator_groups.SimulatorGroup', on_delete=models.CASCADE)
    company = models.ManyToManyField("company.Company", verbose_name="Компания", null=True, blank=True)
    text = models.TextField()
