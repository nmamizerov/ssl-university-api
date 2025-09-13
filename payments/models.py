import requests
import json
import logging
from datetime import datetime, timezone
from copy import deepcopy
from hashlib import sha256

from django.db import models
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.core.exceptions import FieldDoesNotExist

# import logging
# logging.basicConfig(filename='example.log', level=logging.DEBUG)
from backend.settings import HOST_URL

User = get_user_model()


class PromoCode(models.Model):
    simulator = models.ForeignKey(
        "simulators.Simulator", on_delete=models.CASCADE, null=True, blank=True
    )
    slug = models.CharField(max_length=40)
    text = models.TextField(null=True, blank=True)
    price = models.PositiveIntegerField()
    user_set = models.ManyToManyField(User, blank=True)
    expires = models.DateTimeField(null=True, blank=True)
    usage_limit = models.PositiveIntegerField(null=True, blank=True)
    usage_count = models.PositiveIntegerField(default=0)

    def activate(self, user):
        if self.expires and self.expires < datetime.now(timezone.utc):
            return False
        if self.user_set.filter(id=user.id).exists():
            return True
        if self.usage_limit and self.usage_limit <= self.usage_count:
            return False

        self.user_set.add(user)
        self.usage_count += 1
        self.save()
        return True

    def __str__(self):
        return "{}: {}".format(self.slug, str(self.simulator))


class Payment(models.Model):
    CANCELED = 0
    PENDING = 1
    SUCCEEDED = 2
    STATUS_CHOICES = (
        (CANCELED, "canceled"),
        (PENDING, "pending"),
        (SUCCEEDED, "succeeded"),
    )
    TYPE_CHOICES = (
        ("tinkoff", "Тинькофф"),
        ("cloudpayments", "CloudPayments"),
        ("select", "Оплата на своем сайте"),
    )
    PRODUCTS = ("simulator", "subscription")

    simulator = models.ForeignKey(
        "simulators.SimulatorUser", on_delete=models.CASCADE, null=True, blank=True
    )
    subscription = models.ForeignKey(
        "subscriptions.UserSubscription",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    ext_course = models.ForeignKey(
        "ext_course.CourseReg", on_delete=models.SET_NULL, null=True, blank=True
    )
    promo_code = models.ForeignKey(
        PromoCode, on_delete=models.SET_NULL, null=True, blank=True
    )

    creation_time = models.DateTimeField(auto_now_add=True, blank=True)
    sum = models.PositiveIntegerField()
    return_url = models.CharField(max_length=200)
    description = models.CharField(max_length=200, null=True, blank=True)
    is_recurrent = models.BooleanField(default=False)

    is_credit = models.BooleanField(default=False)

    confirmation_url = models.CharField(max_length=200, null=True, blank=True)
    payment_id = models.CharField(max_length=200, null=True, blank=True)

    status = models.IntegerField(default=1, choices=STATUS_CHOICES)
    backend = models.CharField(max_length=30, choices=TYPE_CHOICES, default="tinkoff")

    @property
    def object(self):
        result_name, result_value = None, None
        if self.ext_course is not None:
            return {"name": "course", "value": self.ext_course}
        flag = 0
        for name, value in self:
            if value:
                flag += 1
                result_name, result_value = name, value

        if flag > 1:
            raise ValueError("Оплата может быть привязана только к одному продукту")
        if not flag:
            raise ValueError("Оплата не привязана к какому-либо продукту")

        return {"name": result_name, "value": result_value}

    @property
    def user(self):
        try:
            if self.ext_course is None:
                return self.object["value"].user
            else:
                return self.ext_course
        except AttributeError:
            raise ValueError("Продукт не привязан к пользователю")

    @property
    def product(self):
        try:
            if self.ext_course is not None:
                return self.ext_course.course
            return getattr(self.object["value"], self.object["name"])
        except AttributeError:
            raise ValueError("Выбрана некорректная модель продукта")

    @property
    def credentials(self):
        try:
            if (
                self.product.pay_password
                and self.product.pay_terminal_key
                and self.product.pay_email_company
            ):
                return self.product
            raise AttributeError()
        except AttributeError:
            if self.ext_course is not None:
                if not self.ext_course.course.group:
                    raise AttributeError()
                if (
                    self.ext_course.course.group.pay_password
                    and self.ext_course.course.group.pay_terminal_key
                    and self.ext_course.course.group.pay_email_company
                ):
                    return self.ext_course.course.group
            try:
                if not self.product.group:
                    raise AttributeError()
                if (
                    self.product.group.pay_password
                    and self.product.group.pay_terminal_key
                    and self.product.group.pay_email_company
                ):
                    return self.product.group
            except AttributeError:
                raise ValueError("Модель продукта должна быть привязана к группе")
        raise ValueError("Отсутствуют реквизиты терминала")

    @property
    def vat(self):
        if not self.credentials.vat:
            if self.backend == "tinkoff":
                return "none"
            if self.backend == "cloudpayments":
                return "null"
        return self.credentials.vat

    def _get_token_tinkoff(self, jsn):
        data = deepcopy(jsn)
        data["Password"] = self.credentials.pay_password
        data.pop("Receipt", None)
        data.pop("DATA", None)

        data_items = sorted(list(data.items()), key=lambda item: item[0])
        data_values = [str(val) for key, val in data_items]
        data_string = "".join(data_values)
        return sha256(data_string.encode("utf-8")).hexdigest()

    def _configure_init_json_tinkoff(self):
        payload = {
            "TerminalKey": self.credentials.pay_terminal_key,
            "Amount": int(self.sum * 100),
            "OrderId": f"University+{self.id}",
            "Description": self.product.name,
            "DATA": {"Email": self.user.email},
            "NotificationURL": f"{HOST_URL}/api/payments/complete_tinkoff/",
            "Receipt": {
                "Email": self.user.email,
                "EmailCompany": self.credentials.pay_email_company,
                "Taxation": "usn_income",
                "Items": [
                    {
                        "Name": self.product.name,
                        "Price": int(self.sum * 100),
                        "Quantity": 1,
                        "Amount": int(self.sum * 100),
                        "PaymentMethod": "full_payment",
                        "PaymentObject": "service",
                        "Tax": self.vat,
                    }
                ],
            },
        }

        if self.is_recurrent:
            payload["Recurrent"] = "Y"
            payload["CustomerKey"] = f"University+{self.user.id}"

        payload["Token"] = self._get_token_tinkoff(payload)
        return payload

    def _configure_charge_json_tinkoff(self):
        payload = {
            "TerminalKey": self.credentials.pay_terminal_key,
            "PaymentId": self.payment_id,
            "RebillId": self.object["value"].rebill_ID,
        }

        payload["Token"] = self._get_token_tinkoff(payload)
        return payload

    def _pay_tinkoff(self):
        response = requests.post(
            "https://securepay.tinkoff.ru/v2/Init",
            json=self._configure_init_json_tinkoff(),
        )
        payload = json.loads(response.text)
        logging.debug(self._configure_init_json_tinkoff())
        if not payload["Success"]:
            raise ValueError(payload["Details"])

        self.confirmation_url = payload["PaymentURL"]
        self.payment_id = payload["PaymentId"]
        self.save()

    def _pay_cloudpayments(self):
        self.payment_id = self.id
        self.confirmation_url = f"/api/payments/{HOST_URL}/pay_cloudpayments/"
        self.save()

    def _charge_tinkoff(self):
        response = requests.post(
            "https://securepay.tinkoff.ru/v2/Charge",
            json=self._configure_charge_json_tinkoff(),
        )
        payload = json.loads(response.text)

        if not payload["Success"]:
            raise ValueError(payload["Message"])

    def _init_bank_transaction(self):
        if self.payment_id:
            return

        if self.backend == "tinkoff":
            self._pay_tinkoff()
        elif self.backend == "cloudpayments":
            self._pay_cloudpayments()

    def _charge_bank_transaction(self):
        try:
            if not self.object["value"].rebill_ID:
                raise ValueError("Rebill ID не найдено")
        except AttributeError:
            raise ValueError("Модель должна содержать Rebill ID")

        if self.backend == "tinkoff":
            self._charge_tinkoff()

    def check_bank_transaction_status(self, status, **kwargs):
        if not self.payment_id:
            return None
        if self.status != 1:
            return self.status

        if status in (
            "REJECTED",
            "REFUNDED",
            "Fail",
            "CANCELED",
        ):
            self.status = 0
            self.object["value"].cancel_payment()
        elif status in (
            "CONFIRMED",
            "Authorized",
            "Completed",
            "AUTHORIZED",
            "COMPLETED",
        ):
            self.status = 2
            self.object["value"].finish_payment(
                sum=self.sum, promo_code=self.promo_code, **kwargs
            )

        self.save()
        return self.status

    def pay(self):
        self._init_bank_transaction()
        return {"id": self.id, "confirmation_url": self.confirmation_url}

    def charge(self):
        self._init_bank_transaction()
        self._charge_bank_transaction()

    def __iter__(self):
        field_names = self.PRODUCTS
        for field_name in field_names:
            try:
                self._meta.get_field(field_name)
            except FieldDoesNotExist:
                raise ValueError(f"{field_name} не привязано к оплате")
            value = getattr(self, field_name)
            yield field_name, value

    def __str__(self):
        return f'({self.id}) {self.user}: {self.object["value"]} - {dict(self.STATUS_CHOICES).get(self.status)}'
