from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class CronLog(models.Model):
    title = models.CharField(max_length=255)
    text = models.TextField()
    is_error = models.BooleanField(default=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    def __str__(self):
        return f"{self.title} {str(self.is_error)}"
