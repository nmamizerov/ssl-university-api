from string import Template

from django.db import models
from emails.emails import send_email


class Product(models.Model):
    simulator = models.ForeignKey("simulators.Simulator", on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    cost = models.IntegerField(default=0)
    image = models.ImageField(upload_to='product_images', blank=True, null=True)
    users = models.ManyToManyField("user_profile.User", related_name='users', blank=True)
    template = models.TextField(blank=True, null=True)
    theme = models.CharField(max_length=255, blank=True, null=True)

    def send_email(self, user, email_sender):
        theme = 'Покупка продукта'
        if self.theme:
            theme = self.theme

        template_user = Template(self.template).safe_substitute(product_title=self.title,
                                                                simulator=self.simulator.name,
                                                                first_name=user.first_name,
                                                                last_name=user.last_name)

        send_email(self.simulator.owner.email, "Пользователь с {} купил {}".format(user.email, self.title), theme, email_sender)

        if user.subscribe:
            send_email(user.email, template_user, theme, email_sender)
