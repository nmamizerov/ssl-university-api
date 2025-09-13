from string import Template

from django.core.exceptions import FieldDoesNotExist
from django.db import models
from .emails import send_email


class Email(models.Model):
    ITEMS = (
        'simulator',
        'group',
        'subscription'
    )
    simulator = models.ForeignKey('simulators.Simulator', on_delete=models.CASCADE, blank=True, null=True)
    group = models.ForeignKey('simulator_groups.SimulatorGroup', on_delete=models.CASCADE, blank=True, null=True)
    subscription = models.ForeignKey('subscriptions.Subscription', on_delete=models.CASCADE, blank=True, null=True)

    TYPES = (
        (0, 'Регистрация'),
        (1, 'Покупка'),
        (2, 'Покупка отклонена'),
        (3, 'Продление подписки'),
        (4, 'Отмена подписки'),
        (5, 'Возобновление подписки'),
        (6, 'Успешное продление подписки'),
        (7, 'Рассылка')
    )
    email_type = models.PositiveIntegerField(choices=TYPES, default=0)
    template = models.TextField()
    theme = models.CharField(max_length=255)

    @property
    def object(self):
        result_name, result_value = None, None

        flag = 0
        for name, value in self:
            if value:
                flag += 1
                result_name, result_value = name, value

        if flag > 1:
            raise ValueError('Модель может быть привязана только к одной сущности')
        if not flag:
            raise ValueError('Модель не привязана к какой-либо сущности')

        return {
            'name': result_name,
            'value': result_value
        }

    def send_email(self, user, email_sender, *args, **kwargs):
        if not user.subscribe:
            return

        kwargs[self.object['name']] = self.object['value'].name

        template = Template(self.template).safe_substitute(first_name=user.first_name,
                                                           last_name=user.last_name,
                                                           **kwargs)

        send_email(user.email, template, self.theme, email_sender)

    def __iter__(self):
        field_names = self.ITEMS
        for field_name in field_names:
            try:
                self._meta.get_field(field_name)
            except FieldDoesNotExist:
                raise ValueError(f'{field_name} не привязано к модели')
            value = getattr(self, field_name)
            yield field_name, value

    def __str__(self):
        return f'Type: {self.email_type}, {self.object["name"]}: {self.object["value"]} (ID: {self.id})'
