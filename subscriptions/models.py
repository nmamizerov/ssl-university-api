from datetime import timedelta, datetime, timezone

from django.db import models
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from emails.models import Email
from payments.models import Payment, PromoCode

User = get_user_model()


class Subscription(models.Model):
    group = models.ForeignKey('simulator_groups.SimulatorGroup', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    is_show = models.BooleanField(default=True)
    vat = models.IntegerField(null=True, blank=True)

    price_month = models.PositiveIntegerField(blank=True, null=True)
    price_year = models.PositiveIntegerField(blank=True, null=True)
    price_trial = models.PositiveIntegerField(blank=True, null=True)
    trial_period = models.DurationField(blank=True, null=True)

    is_blog = models.BooleanField(default=False)
    is_club = models.BooleanField(default=False)

    def send_email(self, type, user, price=None):
        email = Email.objects.filter(subscription=self, email_type=type).first()
        if email:
            email.send_email(user=user, email_sender=self.group.email_sender, price=price)

    def __str__(self):
        return f'{self.name} ({self.id})'


class UserSubscription(models.Model):
    TYPES = (
        (0, 'Нет подписки'),
        (1, 'Заполнен профиль'),
        (2, 'Базовая подписка'),
        (3, 'Попытка оплаты пробной подписки'),
        (4, 'Попытка оплаты полной подписки'),
        (5, 'Пробный период'),
        (6, 'Платная подписка')
    )
    type = models.IntegerField(default=0, choices=TYPES)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subscription = models.ForeignKey(Subscription, on_delete=models.SET_NULL, blank=True, null=True)
    resubscribe = models.BooleanField(default=False)
    resubscribe_try = models.BooleanField(default=False)
    alert = models.BooleanField(default=False)
    price = models.PositiveIntegerField(blank=True, null=True)
    period = models.DurationField(blank=True, null=True)
    valid_until = models.DateTimeField(blank=True, null=True)
    trial_expired = models.BooleanField(default=False)
    rebill_ID = models.CharField(max_length=255, blank=True, null=True)
    trainer = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name="trainer_user")

    def pay(self, **kwargs):
        if self.type < 2:
            raise ValueError('Требуется создать профиль')

        if 'period' in kwargs:
            if kwargs['period'] == 'month':
                self.period = timedelta(days=30)
                self.price = self.subscription.price_month
                if self.type < 5:
                    self.type = 4

            elif kwargs['period'] == 'year':
                self.period = timedelta(days=365)
                self.price = self.subscription.price_year
                if self.type < 5:
                    self.type = 4
            elif kwargs['period'] == 'trial':
                if self.trial_expired:
                    raise ValueError('Ваш пробный период уже истек')

                self.period = self.subscription.trial_period
                self.price = self.subscription.price_trial
                self.type = 3
            else:
                raise ValueError('Неверно указан период')

        promo_code = None
        if 'promo_code' in kwargs:
            pass

        self.save()

        payment = Payment.objects.create(
            description=f'Подписка Soft Skills Lab: {self.subscription.name}' if not promo_code else 'Promo code: {}'.format(promo_code.slug),
            return_url='https://skillslab.center',
            sum=self.price,
            promo_code=promo_code,
            subscription=self,
            is_recurrent=True
        )
        return payment.pay()

    def charge(self):
        if self.type < 5:
            return

        if not self.valid_until:
            raise ValueError('Valid_until не определено')

        if self.valid_until - datetime.now(timezone.utc) <= timedelta(days=3) and not self.alert and self.resubscribe:
            self.subscription.send_email(3, self.user)
            self.alert = True
            self.save()
            return

        if self.valid_until - datetime.now(timezone.utc) > timedelta(days=0):
            return

        if not self.resubscribe:
            self.resubscribe_try = False
            self.rebill_ID = None
            self.type = 2
            self.save()
            return

        if self.type == 5:
            self.type = 6
            self.price = self.subscription.price_month
            self.period = timedelta(days=30)

        promo_code = None
        if self.resubscribe_try:
            return
        self.resubscribe_try = True
        self.save()

        payment = Payment.objects.create(
            description=f'Подписка Soft Skills Lab: {self.subscription.name}' if not promo_code else 'Promo code: {}'.format(promo_code.slug),
            return_url='https://skillslab.center',
            sum=self.price,
            promo_code=promo_code,
            subscription=self
        )
        payment.charge()

    def finish_payment(self, **kwargs):
        if self.type == 3 or self.type == 4:
            self.subscription.send_email(1, self.user, price=self.price)
        elif self.type == 5 or self.type == 6:
            self.subscription.send_email(6, self.user, price=self.price)

        self.valid_until = datetime.now(timezone.utc) + self.period
        self.resubscribe = True
        self.alert = False

        if self.type == 3:
            self.trial_expired = True
            self.type = 5
        elif self.type == 4:
            self.trial_expired = True
            self.type = 6

        if 'rebill_ID' in kwargs and kwargs['rebill_ID']:
            self.rebill_ID = kwargs['rebill_ID']
        
        self.resubscribe_try = False
        self.save()

    def cancel_payment(self):
        self.resubscribe = False
        self.alert = False
        self.type = 2
        self.resubscribe_try = False
        if self.rebill_ID:
            self.rebill_ID = None

        self.save()

    def __str__(self):
        return f'User: {self.user}, Type: {self.type}, ({self.id})'
