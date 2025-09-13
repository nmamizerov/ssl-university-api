from django.db import models
from django.contrib.auth import get_user_model

from emails.models import Email
from payments.models import Payment

User = get_user_model()


class SimulatorGroup(models.Model):
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='owned_simulator_group_set')
    name = models.CharField(max_length=200, default="Основная группа")

    email_sender = models.CharField(max_length=30, blank=True, null=True)

    auth_facebook_key = models.CharField(max_length=255, blank=True, null=True)
    auth_facebook_secret = models.CharField(max_length=255, blank=True, null=True)
    auth_vk_key = models.CharField(max_length=255, blank=True, null=True)
    auth_vk_secret = models.CharField(max_length=255, blank=True, null=True)

    pay_terminal_key = models.CharField(null=True, blank=True, max_length=255)
    pay_password = models.CharField(null=True, blank=True, max_length=255)
    pay_email_company = models.CharField(null=True, blank=True, max_length=255)
    pay_type = models.CharField(max_length=255, default='tinkoff', choices=Payment.TYPE_CHOICES)
    pay_url = models.CharField(max_length=255, null=True, blank=True)
    vat = models.IntegerField(blank=True, null=True)

    def send_email(self, type, user, password=None):
        email = Email.objects.filter(group=self, email_type=type).first()
        if email:
            email.send_email(user=user, email_sender=self.email_sender, password=password)

    def __str__(self):
        return '({}) {}'.format(self.id, self.name)
