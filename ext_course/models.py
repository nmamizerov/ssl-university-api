from django.db import models
from bot.views import send_ext_course_info
import requests
from datetime import datetime, timedelta
from django.utils import timezone
import logging, json

logger = logging.getLogger(__name__)


# logging.basicConfig(filename='example.log', level=logging.DEBUG)
def refresh_token(refresh):

    url = "https://sslklimenko.amocrm.ru/oauth2/access_token"
    data = {
        "client_id": "3401fa29-4301-4545-9864-9cbe6f892f7e",
        "client_secret": "wiM5E7mAfvd7Tg0g9V3FKCcKna8dHrK5F92Zmoq6FCgDzyX9lhV5n4UAT1Wh8UJq",
        "grant_type": "refresh_token",
        "refresh_token": refresh,
        "redirect_uri": "https://api.university.skillslab.center/api/amocrm",
    }
    request = requests.post(url, data=data)
    request_dict = json.loads(request.text)
    logger.debug(request.status_code)
    logger.debug(request_dict)
    refresh_code = request_dict["refresh_token"]
    access_token = request_dict["access_token"]
    expires_in = request_dict["expires_in"]
    AmoData.objects.create(
        refresh=refresh_code, expires=expires_in, access=access_token
    )
    return access_token


class AmoData(models.Model):
    refresh = models.TextField(blank=True, null=True)
    expires = models.DateTimeField(auto_now_add=True)
    refresh_time = models.IntegerField(default=86400)
    access = models.TextField(blank=True, null=True)


# Create your models here.
class Course(models.Model):
    name = models.CharField(max_length=255, verbose_name="Название")
    description = models.TextField(blank=True)
    theme = models.CharField(max_length=255, verbose_name="Тема", blank=True)
    email = models.TextField(blank=True)
    price = models.FloatField()
    telegram = models.TextField(blank=True)
    amo_pipe = models.IntegerField(blank=True, null=True)
    amo_paid_status = models.IntegerField(blank=True, null=True)
    group = models.ForeignKey(
        "simulator_groups.SimulatorGroup",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )

    def __str__(self):
        return f"{self.name}"


class CoursePromocode(models.Model):
    text = models.CharField(max_length=255, verbose_name="Промокод")
    course = models.ForeignKey(
        "Course", on_delete=models.SET_NULL, blank=True, null=True
    )
    price = models.FloatField()

    def __str__(self):
        return f"{self.text}"


class CourseReg(models.Model):
    name = models.CharField(max_length=255)
    email = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=30, blank=True, null=True)
    additional = models.TextField(blank=True, null=True)
    course = models.ForeignKey(
        "Course", on_delete=models.SET_NULL, blank=True, null=True
    )
    promocode = models.CharField(max_length=130, blank=True, null=True)
    final_price = models.FloatField(blank=True, null=True)
    paid = models.BooleanField(default=False)
    to_amo = models.BooleanField(default=True)
    in_amo = models.BooleanField(default=False)
    amo_id = models.TextField(blank=True, null=True)
    utm_campaign = models.TextField(blank=True, null=True)
    utm_source = models.TextField(blank=True, null=True)
    utm_medium = models.TextField(blank=True, null=True)
    utm_content = models.TextField(blank=True, null=True)
    utm_term = models.TextField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)

    def unsuccess_payment(self):
        return

    def get_amo_access_token(self):
        amo = AmoData.objects.last()
        x = amo.expires + timedelta(seconds=amo.refresh_time)

        if amo.access and x > timezone.now():
            access = amo.access
        else:
            access = refresh_token(amo.refresh)
        return access

    def success_payment(self, is_credit=False):
        self.paid = True
        self.save()
        if (
            self.course.amo_pipe is not None
            and self.amo_id is not None
            and self.course.amo_paid_status is not None
        ):
            access = self.get_amo_access_token()
            api_call_headers = {
                "Authorization": "Bearer " + access,
                "Content-Type": "application/json",
            }
            url = f"https://sslklimenko.amocrm.ru/api/v4/leads/{self.amo_id}"
            text = {"status_id": self.course.amo_paid_status}
            jsonStr = json.dumps(text)
            # logging.debug(jsonStr)
            request = requests.patch(url, headers=api_call_headers, data=jsonStr)
            request_dict = json.loads(request.text)

            # logging.debug(request_dict)
        if self.course.telegram is not None:
            text = f"Успешная оплата\nкурс: {self.course.name}\nname: {self.name}\nemail:{self.email}\nphone: {self.phone}\nextra: {self.additional}\npromocode {self.promocode}\nfinalPrice {str(self.final_price)}₽\nis_credit: {str(is_credit)}"
            send_ext_course_info(
                self.course.telegram,
                text,
            )
        return

    def start(self, is_credit=False):
        if self.course.amo_pipe is not None:
            access = self.get_amo_access_token()
            api_call_headers = {
                "Authorization": "Bearer " + access,
                "Content-Type": "application/json",
            }
            url = "https://sslklimenko.amocrm.ru/api/v4/leads/complex"
            text = [
                {
                    "name": f"{self.name}: {self.course.name}",
                    "price": int(self.final_price),
                    "pipeline_id": self.course.amo_pipe,
                    "_embedded": {
                        "contacts": [
                            {
                                "first_name": self.name,
                                "custom_fields_values": [
                                    {
                                        "field_code": "PHONE",
                                        "values": [
                                            {"enum_code": "WORK", "value": self.phone}
                                        ],
                                    },
                                    {
                                        "field_id": 1057621,
                                        "values": [{"value": self.phone}],
                                    },
                                    {
                                        "field_code": "EMAIL",
                                        "values": [
                                            {"enum_code": "WORK", "value": self.email}
                                        ],
                                    },
                                ],
                            }
                        ]
                    },
                    "custom_fields_values": [
                        {"field_id": 690079, "values": [{"value": self.promocode}]},
                        {
                            "field_code": "UTM_SOURCE",
                            "values": [{"value": self.utm_source}],
                        },
                        {
                            "field_code": "UTM_MEDIUM",
                            "values": [{"value": self.utm_medium}],
                        },
                        {
                            "field_code": "UTM_CAMPAIGN",
                            "values": [{"value": self.utm_campaign}],
                        },
                        {
                            "field_code": "UTM_CONTENT",
                            "values": [{"value": self.utm_content}],
                        },
                        {
                            "field_code": "UTM_TERM",
                            "values": [{"value": self.utm_term}],
                        },
                        {
                            "field_code": "IS_CREDIT",
                            "values": [{"value": str(is_credit)}],
                        },
                    ],
                }
            ]

            jsonStr = json.dumps(text)
            request = requests.post(url, headers=api_call_headers, data=jsonStr)

            request_dict = json.loads(request.text)

            # logging.debug(request_dict)
            if "validation-errors" not in request_dict:
                self.amo_id = request_dict[0]["id"]
                self.in_amo = True
                self.save()
        if self.course.telegram is not None:
            send_ext_course_info(
                self.course.telegram,
                f"Первичная заявка\nкурс: {self.course.name}\nname: {self.name}\nemail:{self.email}\nphone: {self.phone}\nextra: {self.additional}\npromocode {self.promocode}\nfinalPrice {str(self.final_price)}₽\nutm_campaign: {self.utm_campaign}\nutm_medium: {self.utm_medium}\nutm_content: {self.utm_content}\nutm_source: {self.utm_source}\nis_credit {str(is_credit)}",
            )

    def __str__(self):
        return f"{self.name}"
