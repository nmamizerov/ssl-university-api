import json
import logging
from copy import copy
from datetime import datetime
import requests
import uuid

from django.contrib.auth import get_user_model, password_validation
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect
from django.db import IntegrityError
from django.db.models import Q
from django.shortcuts import get_object_or_404
from backend.application_viewset import AdminApplicationViewSet
from rest_framework import mixins, viewsets, status, serializers
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.renderers import StaticHTMLRenderer
from datetime import timedelta, datetime, timezone

from backend.settings import HOST_URL
from knox.models import AuthToken

from emails.emails import send_email
from places.models import Place, PlaceUser
from simulator_groups.models import SimulatorGroup
from simulators.models import Simulator, SimulatorUser
from subscriptions.models import UserSubscription, Subscription
from company.models import CompanyEmails
from payments.models import Payment
from user_profile.permissions import UsersPermissions
from .models import AuthAttempt
from .serializers import (
    AdminUserSerializer,
    UserCreateSerializer,
    UserInfoSerializer,
    UserStatisticSerializer,
    AuthAttemptSerializer,
)
from lessons.models import Lesson, UserLessonProgress

User = get_user_model()
logger = logging.getLogger("django.server")
from rest_framework.views import APIView
import random
import string


# import logging
# logging.basicConfig(filename='example.log', level=logging.DEBUG)
def rand_slug():
    return "".join(
        random.choice(string.ascii_letters + string.digits) for _ in range(8)
    )


def auth(
    content,
    is_login=False,
    check_login=False,
    need_temporary_code=False,
    need_password=False,
    send_password=False,
    check_password=True,
    is_auto_login=False,
    backend="standard",
):
    # Получение данных
    if "token" in content:
        simulator = Simulator.objects.get(token=content["token"])
        group = simulator.group
    elif "simulator" in content:
        simulator = Simulator.objects.get(id=content["simulator"])
        group = simulator.group
    elif "group" in content:
        simulator = None
        group = SimulatorGroup.objects.get(id=content["group"])
    elif "user" in content:
        simulator = None
        group = None
    else:
        raise ValueError("Группа или симулятор не предоставлены!")

    if "password" in content:
        password = content["password"]
    else:
        password = uuid.uuid4().hex[:16]

    email = None
    if "email" in content:
        email = content["email"]

        try:
            serializers.EmailField().run_validators(email)
        except serializers.ValidationError:
            raise ValueError("Почта указана некорректно")

    # Социальный ID
    user_id = None
    if "user_id" in content:
        user_id = str(content["user_id"])

    if group:
        postfix = "+{}".format(group.id)

    # Формирование фильтра и username
    if backend == "facebook":
        filter = Q(facebook_id=user_id + postfix)
        username = "facebook+" + user_id + postfix
    elif backend == "vk":
        filter = Q(vk_id=user_id + postfix)
        username = "vk+" + user_id + postfix
    else:
        if "user" in content:
            filter = Q(id=content["user"].id)

            if email and group:
                username = email + postfix
            else:
                username = None

            if not is_login:
                raise ValueError("Неизвестная ошибка")
        else:
            if not email:
                raise ValueError("Почта необходима в этом запросе!")

            filter = Q(username=email + postfix)
            username = email + postfix

    is_exists = (
        User.objects.filter(filter).exists()
        or email
        and SimulatorUser.objects.filter(
            user__email=email, simulator=simulator
        ).exists()
    )

    # Получение пользователя
    if is_exists:
        if User.objects.filter(filter).exists():
            user = User.objects.get(filter)
        else:
            user = SimulatorUser.objects.get(
                user__email=email, simulator=simulator
            ).user

    # Авторизация
    if is_auto_login:
        if not is_exists:
            raise ValueError("Такой учетной записи не существует")
        user = SimulatorUser.objects.get(user__email=email, simulator=simulator).user
    else:
        if is_login:
            if not is_exists:
                raise ValueError("Такой учетной записи не существует")

            if check_password and not user.check_password(password):
                raise ValueError("Неверный пароль")
        # Регистрация
        elif is_exists:
            if not check_login:
                raise ValueError("Этот пользователь уже зарегистрирован")

            # Авторизация (check_login запросил проверку, и она пройдена - пользователь уже зарегистрирован)
            is_login = True
        else:
            user = User(password=password, username=username)
            user.set_password(password)
            user.save()

    # Сохранение данных
    if username:
        user.username = username
    if email:
        user.email = email
    if user_id:
        if backend == "facebook":
            user.facebook_id = user_id + postfix
        elif backend == "vk":
            user.vk_id = user_id + postfix
    if "first_name" in content:
        user.first_name = content["first_name"]
    if "last_name" in content:
        user.last_name = content["last_name"]
    if "male" in content:
        user.male = True if content["male"] == "true" else False
    if need_temporary_code:
        user.temporary_code = uuid.uuid4().hex[:8]
    user.is_active = True

    try:
        user.save()
    except IntegrityError:
        raise ValueError("Пользователь с таким email уже зарегистрирован")
    except Exception as error:
        raise ValueError(str(error))
    if is_auto_login:
        return user
    if is_login:
        return user

    # Регистрация во всех симуляторах группы
    simulators = Simulator.objects.filter(group=group)
    for item in simulators:
        simulator_user = SimulatorUser(user=user, simulator=item)
        if not item.onboarding_skip:
            simulator_user.current_page = item.onboarding
        simulator_user.save()

    # Оплата симулятора
    if "set_paid" in content and content["set_paid"]:
        simulator_user = SimulatorUser.objects.get(user=user, simulator=simulator)
        simulator_user.simulator_paid = True
        simulator_user.save()

    # Отправка письма
    if email:
        if send_password:
            group.send_email(0, user, password)
        else:
            group.send_email(0, user)

    if need_password:
        return user, password
    return user


class CheckEmailSub(APIView):
    def get(self, request):
        email = request.GET.get("email")
        user_sub = UserSubscription.objects.filter(user__email=email).first()
        if user_sub is None or user_sub.type < 5 or not user_sub.subscription.is_blog:
            return Response({"is_paid": False}, 200)
        else:
            return Response({"is_paid": True, "till": user_sub.valid_until}, 200)


class ExternalTrialRegistration(APIView):
    def post(self, request):
        if (
            "token" in request.data
            and request.data["token"] == "askjdlkajldsadk01890923"
        ):
            email = request.data["email"]
            user = User.objects.filter(email=email).first()
            sub = Subscription.objects.filter(pk=request.data["subscription"]).first()
            if sub is None:
                return Response(
                    "Нет такой подписки", status=status.HTTP_401_UNAUTHORIZED
                )
            if user is not None:
                u_s = UserSubscription.objects.filter(user=user).first()
                if u_s.type >= 5 or u_s.trial_expired:
                    return Response(
                        "Пользователь уже использовал пробный период",
                        status=status.HTTP_401_UNAUTHORIZED,
                    )
                try:
                    u_s.subscription = sub
                    u_s.save()
                    payload = u_s.pay(period=request.data["period"])
                    return Response(
                        {"exist": True, "payload": payload}, status=status.HTTP_200_OK
                    )
                except ValueError as error:
                    return Response(
                        {"detail": str(error)}, status=status.HTTP_400_BAD_REQUEST
                    )

            user = User.objects.create_user(
                username=request.data["username"], password=request.data["password"]
            )
            user.first_name = request.data["first_name"]
            user.last_name = request.data["last_name"]
            user.email = email
            user.save()
            send_email(
                user.email,
                """
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">
<html lang="en" xmlns="http://www.w3.org/1999/xhtml" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office">

<head>
 <meta charset="utf-8">
 <meta name="viewport" content="width=device-width">
 <meta http-equiv="X-UA-Compatible" content="IE=edge">
 <meta name="x-apple-disable-message-reformatting">
 <meta name="format-detection" content="telephone=no,address=no,email=no,date=no,url=no">
 <title>1920 Success_email</title>

 <style>
  html {
      margin: 0 !important;
      padding: 0 !important;
  }
  
  * {
      -ms-text-size-adjust: 100%;
      -webkit-text-size-adjust: 100%;
  }
  
  
  td {
      vertical-align: top;
      mso-table-lspace: 0pt !important;
      mso-table-rspace: 0pt !important;
  }
  
  
  a {
      text-decoration: none;
  }
  
  
  img {
      -ms-interpolation-mode:bicubic;
  }
  
  
  
  
  @media only screen and (min-device-width: 320px) and (max-device-width: 374px) {
      u ~ div .email-container {
          min-width: 320px !important;
      }
  }
  
  @media only screen and (min-device-width: 375px) and (max-device-width: 413px) {
      u ~ div .email-container {
          min-width: 375px !important;
      }
  }
  
  @media only screen and (min-device-width: 414px) {
      u ~ div .email-container {
          min-width: 414px !important;
      }
  }
  
 </style>
 <!--[if gte mso 9]>
        <xml>
            <o:OfficeDocumentSettings>
                <o:AllowPNG/>
                <o:PixelsPerInch>96</o:PixelsPerInch>
            </o:OfficeDocumentSettings>
        </xml>
        <![endif]-->
 <style>
  @media only screen and (max-device-width: 400px), only screen and (max-width: 400px) {
  
      .eh {
          height:auto !important;
      }
  
      .desktop {
          display: none !important;
          height: 0 !important;
          margin: 0 !important;
          max-height: 0 !important;
          overflow: hidden !important;
          padding: 0 !important;
          visibility: hidden !important;
          width: 0 !important;
      }
  
      .mobile {
          display: block !important;
          width: auto !important;
          height: auto !important;
          float: none !important;
      }
  
  
          .email-container {
              width: 100% !important;
              margin: auto !important;
          }
  
  
          .stack-column,
          .stack-column-center {
              display: block !important;
              width: 100% !important;
              max-width: 100% !important;
              direction: ltr !important;
          }
  
          .stack-column-center {
              text-align: center !important;
          }
  
           
          
  
          .center-on-narrow {
              text-align: center !important;
              display: block !important;
              margin-left: auto !important;
              margin-right: auto !important;
              float: none !important;
          }
          table.center-on-narrow {
              display: inline-block !important;
          }
  
      }
  
 </style>
</head>

<body width="100%" style="margin: 0; padding: 0 !important; mso-line-height-rule: exactly;">
 <div style="background-color:#f5f5f5">
  <!--[if gte mso 9]>
                <v:background xmlns:v="urn:schemas-microsoft-com:vml" fill="t">
                <v:fill type="tile" color="#f5f5f5"/>
                </v:background>
                <![endif]-->
  <table width="100%" cellpadding="0" cellspacing="0" border="0">
   <tr>
    <td valign="top" align="center">
     <table bgcolor="#fbfcfe" style="margin: 0 auto;" align="center" id="brick_container" cellspacing="0" cellpadding="0" border="0" width="480" class="email-container">
      <tr>
       <td class="desktop">
        <table cellspacing="0" cellpadding="0" border="0">
         <tr>
          <td width="40">
           <div style="width:40px">&nbsp;</div>
          </td>
          <td width="400" style="padding-right:40px">
           <div style="height:64px;line-height:64px;font-size:64px;width:400px">&nbsp;</div>
           <table cellspacing="0" cellpadding="0" border="0">
            <tr>
             <td style="padding-right:160px;padding-left:160px;">
              <table cellspacing="0" cellpadding="0" border="0">
               <tr>
                <td width="80" style="   ">
                 <table width="100%" cellspacing="0" cellpadding="0" border="0">
                  <tr>
                   <td>
                    <img src="https://newapi.mysimulator.ru/media/cyW1E5vkQt4LMymVoo8QeQSaakVgCe.png" width="80" border="0" style="; height:auto;margin:auto;display:block;">
                   </td>
                  </tr>
                 </table>
                </td>
               </tr>
              </table>
             </td>
            </tr>
            <tr>
             <td>
              <div style="height:40px;line-height:40px;font-size:40px;width:400px">&nbsp;</div>
              <table cellspacing="0" cellpadding="0" border="0">
               <tr>
                <td width="400" style="   ">
                 <table width="100%" cellspacing="0" cellpadding="0" border="0">
                  <tr>
                   <td width="400">
                    <table cellspacing="0" cellpadding="0" border="0">
                     <tr>
                      <td style="max-width:400px;text-align:center; ;">
                       <table cellspacing="0" cellpadding="0" border="0">
                        <tr>
                         <td style="text-align:center;" width="400">
                          <div style="line-height:26px"><span style="color: #16171b;line-height:26px;font-family:Arial, Helvetica, Arial, sans-serif; font-size:24px;text-transform: uppercase;text-align:center;">подписка успешно оформлена</span></div>
                         </td>
                        </tr>
                       </table>
                      </td>
                     </tr>
                     <tr>
                      <td style="max-width:400px;text-align:center; ;">
                       <div style="height:24px;line-height:24px;font-size:24px;width:400px">&nbsp;</div>
                       <table cellspacing="0" cellpadding="0" border="0">
                        <tr>
                         <td style="text-align:center;" width="400">
                          <div style="line-height:22px"><span style="color: #16171b;line-height:22px;font-family:Arial, Helvetica, Arial, sans-serif; font-size:16px;text-align:center;">Для продолжения вам нужно авторизироваться по одноразовому паролю<br></span><span style="color: #16171b;line-height:22px;font-family:Arial, Helvetica, Arial, sans-serif; font-size:16px;text-align:center;font-weight: 700;">Логин: </span><span style="color: #16171b;line-height:22px;font-family:Arial, Helvetica, Arial, sans-serif; font-size:16px;text-align:center;">"""
                + user.email
                + """<br></span><span style="color: #16171b;line-height:22px;font-family:Arial, Helvetica, Arial, sans-serif; font-size:16px;text-align:center;font-weight: 700;">Пароль: </span><span style="color: #16171b;line-height:22px;font-family:Arial, Helvetica, Arial, sans-serif; font-size:16px;text-align:center;">"""
                + request.data["password"]
                + """</span></div>
                         </td>
                        </tr>
                       </table>
                      </td>
                     </tr>
                    </table>
                   </td>
                  </tr>
                 </table>
                </td>
               </tr>
              </table>
             </td>
            </tr>
            <tr>
             <td>
              <div style="height:40px;line-height:40px;font-size:40px;width:400px">&nbsp;</div>
              <table cellspacing="0" cellpadding="0" border="0">
               <tr>
                <td width="400" style="   ">
                 <table width="100%" cellspacing="0" cellpadding="0" border="0">
                  <tr>
                   <td width="400">
                    <table cellspacing="0" cellpadding="0" border="0">
                     <tr>
                      <td style="max-width:400px;text-align:center; ;">
                       <table cellspacing="0" cellpadding="0" border="0">
                        <tr>
                         <td style="text-align:center;" width="400">
                          <div style="line-height:22px"><span style="color: #16171b;line-height:22px;font-family:Arial, Helvetica, Arial, sans-serif; font-size:16px;text-align:center;">После авторизации не забудьте поменять пароль в личном кабинете</span></div>
                         </td>
                        </tr>
                       </table>
                      </td>
                     </tr>
                    </table>
                   </td>
                  </tr>
                 </table>
                </td>
               </tr>
              </table>
             </td>
            </tr>
            <tr>
                          <td style="max-width:400px;text-align:center; ;">
                            <div style="height:40px;line-height:40px;font-size:40px;width:400px">
                              &nbsp;</div>
                            <table cellspacing="0" cellpadding="0" border="0">
                              <tr>
                                <td style="text-align:center;" width="400">
                                  <div style="line-height:22px"><span
                                      style="color: #16171b;line-height:22px;font-family:Arial, Helvetica, Arial, sans-serif; font-size:16px;text-align:center;">Переходите
                                      в
                                    </span>
                                    <a href="https://t.me/ssl_onboarding_bot" target="_blank"
                                      rel="noopener noreferrer"><span
                                        style="color: #0038ff;line-height:22px;font-family:Arial, Helvetica, Arial, sans-serif; font-size:16px;text-decoration: underline;text-align:center;">тг-бота
                                      </span>
                                    </a>

                                    <span
                                      style="color: #000000;line-height:22px;font-family:Arial, Helvetica, Arial, sans-serif; font-size:16px;text-align:center;">,
                                      который введет вас в курс дела и поможет
                                      персонализировать процесс обучения </span>
                                  </div>
                                </td>
                              </tr>
                            </table>
                          </td>
                        </tr>
                        <tr>
                          <td>
                            <div style="height:40px;line-height:40px;font-size:40px;width:400px">
                              &nbsp;</div>
                            <table cellspacing="0" cellpadding="0" border="0">
                              <tr>
                                <td width="400" style="   ">
                                  <table width="100%" cellspacing="0" cellpadding="0" border="0">
                                    <tr>
                                      <td width="400">
                                        <table cellspacing="0" cellpadding="0" border="0">
                                          <tr>
                                            <td style="max-width:400px;text-align:center; ;">
                                              <table cellspacing="0" cellpadding="0" border="0">
                                                <tr>
                                                  <td style="text-align:center;" width="400">
                                                    <div style="line-height:22px">
                                                      <span
                                                        style="color: #16171b;line-height:22px;font-family:Arial, Helvetica, Arial, sans-serif; font-size:16px;text-align:center;">А
                                                        еще у
                                                        нас есть
                                                        закрытый
                                                      </span>
                                                      <a href="https://t.me/sslpractice" target="_blank"
                                                        rel="noopener noreferrer"><span
                                                          style="color: #163dd7;line-height:22px;font-family:Arial, Helvetica, Arial, sans-serif; font-size:16px;text-decoration: underline;text-align:center;">телеграмм-канал,
                                                        </span></a>
                                                      <span
                                                        style="color: #000000;line-height:22px;font-family:Arial, Helvetica, Arial, sans-serif; font-size:16px;text-align:center;">где
                                                        регулярно
                                                        выходят
                                                        разборы
                                                        кейсов и
                                                        другая
                                                        полезная
                                                        информация
                                                        -
                                                        подписывайтесь</span>
                                                    </div>
                                                  </td>
                                                </tr>
                                              </table>
                                            </td>
                                          </tr>
                                        </table>
                                      </td>
                                    </tr>
                                  </table>
                                </td>
                              </tr>
                            </table>
                          </td>
                        </tr>
            <tr>
             <td>
              <div style="height:40px;line-height:40px;font-size:40px;width:400px">&nbsp;</div>
              <a href="https://skillslab.center/"><img src="https://newapi.mysimulator.ru/media/xcwLG0IsqFPi03HOtPnmffYp9stVDp.png" width="400" border="0" style="width: 100%; height:auto;margin:auto;display:block;"></a>
             </td>
            </tr>
           </table>
           <div style="height:64px;line-height:64px;font-size:64px;width:400px">&nbsp;</div>
          </td>
         </tr>
        </table>
       </td>
      </tr>
      <!--[if !mso]><!-->
      <tr>
       <td class="mobile" align="center" style="display: none; width: 0; height: 0;">
        <table cellspacing="0" cellpadding="0" border="0">
         <tr>
          <td width="16">
           <div style="width:16px">&nbsp;</div>
          </td>
          <td width="288" style="padding-right:16px">
           <div style="height:40px;line-height:40px;font-size:40px;width:288px">&nbsp;</div>
           <table cellspacing="0" cellpadding="0" border="0">
            <tr>
             <td style="padding-right:104px;padding-left:104px;">
              <table cellspacing="0" cellpadding="0" border="0">
               <tr>
                <td width="80" style="   ">
                 <table width="100%" cellspacing="0" cellpadding="0" border="0">
                  <tr>
                   <td>
                    <img src="https://newapi.mysimulator.ru/media/wCKaJ6O47j3yK9MQz9CHITdXKL7bhU.png" width="80" border="0" style="; height:auto;margin:auto;display:block;">
                   </td>
                  </tr>
                 </table>
                </td>
               </tr>
              </table>
             </td>
            </tr>
            <tr>
             <td>
              <div style="height:40px;line-height:40px;font-size:40px;width:288px">&nbsp;</div>
              <table cellspacing="0" cellpadding="0" border="0">
               <tr>
                <td width="288" style="   ">
                 <table width="100%" cellspacing="0" cellpadding="0" border="0">
                  <tr>
                   <td width="288">
                    <table cellspacing="0" cellpadding="0" border="0">
                     <tr>
                      <td style="max-width:288px;text-align:center; ;">
                       <table cellspacing="0" cellpadding="0" border="0">
                        <tr>
                         <td style="text-align:center;" width="288">
                          <div style="line-height:26px"><span style="color: #16171b;line-height:26px;font-family:Arial, Helvetica, Arial, sans-serif; font-size:24px;text-transform: uppercase;text-align:center;">подписка успешно оформлена</span></div>
                         </td>
                        </tr>
                       </table>
                      </td>
                     </tr>
                     <tr>
                      <td style="max-width:288px;text-align:center; ;">
                       <div style="height:24px;line-height:24px;font-size:24px;width:288px">&nbsp;</div>
                       <table cellspacing="0" cellpadding="0" border="0">
                        <tr>
                         <td style="text-align:center;" width="288">
                          <div style="line-height:22px"><span style="color: #16171b;line-height:22px;font-family:Arial, Helvetica, Arial, sans-serif; font-size:16px;text-align:center;">Для продолжения вам нужно авторизироваться по одноразовому паролю<br></span><span style="color: #16171b;line-height:22px;font-family:Arial, Helvetica, Arial, sans-serif; font-size:16px;text-align:center;font-weight: 700;">Логин: </span><span style="color: #16171b;line-height:22px;font-family:Arial, Helvetica, Arial, sans-serif; font-size:16px;text-align:center;">"""
                + user.email
                + """<br></span><span style="color: #16171b;line-height:22px;font-family:Arial, Helvetica, Arial, sans-serif; font-size:16px;text-align:center;font-weight: 700;">Пароль: </span><span style="color: #16171b;line-height:22px;font-family:Arial, Helvetica, Arial, sans-serif; font-size:16px;text-align:center;">"""
                + request.data["password"]
                + """</span></div>
                          
                         </td>
                        </tr>
                       </table>
                      </td>
                     </tr>
                     <tr>
                      <td style="max-width:288px;text-align:center; ;">
                       <div style="height:24px;line-height:24px;font-size:24px;width:288px">&nbsp;</div>
                       <table cellspacing="0" cellpadding="0" border="0">
                        <tr>
                         <td style="text-align:center;" width="288">
                          <div style="line-height:22px"><span style="color: #16171b;line-height:22px;font-family:Arial, Helvetica, Arial, sans-serif; font-size:16px;text-align:center;">После авторизации не забудьте поменять пароль в личном кабинете</span></div>
                         </td>
                        </tr>
                       </table>
                      </td>
                     </tr>
                     <tr>
                      <td>
                       <div style="height:24px;line-height:24px;font-size:24px;width:288px">&nbsp;</div>
                       <a href="https://skillslab.center/"><img src="https://newapi.mysimulator.ru/media/LllAyPecnv5L7JPSh1YF8s1SMXetTv.png" width="288" border="0" style="width: 100%; height:auto;margin:auto;display:block;"></a>
                      </td>
                     </tr>
                    </table>
                   </td>
                  </tr>
                 </table>
                </td>
               </tr>
              </table>
             </td>
            </tr>
            <tr>
                          <td style="max-width:400px;text-align:center; ;">
                            <div style="height:40px;line-height:40px;font-size:40px;width:400px">
                              &nbsp;</div>
                            <table cellspacing="0" cellpadding="0" border="0">
                              <tr>
                                <td style="text-align:center;" width="400">
                                  <div style="line-height:22px"><span
                                      style="color: #16171b;line-height:22px;font-family:Arial, Helvetica, Arial, sans-serif; font-size:16px;text-align:center;">Переходите
                                      в
                                    </span>
                                    <a href="https://t.me/ssl_onboarding_bot" target="_blank"
                                      rel="noopener noreferrer"><span
                                        style="color: #0038ff;line-height:22px;font-family:Arial, Helvetica, Arial, sans-serif; font-size:16px;text-decoration: underline;text-align:center;">тг-бота
                                      </span>
                                    </a>

                                    <span
                                      style="color: #000000;line-height:22px;font-family:Arial, Helvetica, Arial, sans-serif; font-size:16px;text-align:center;">,
                                      который введет вас в курс дела и поможет
                                      персонализировать процесс обучения </span>
                                  </div>
                                </td>
                              </tr>
                            </table>
                          </td>
                        </tr>
                        <tr>
                          <td>
                            <div style="height:40px;line-height:40px;font-size:40px;width:400px">
                              &nbsp;</div>
                            <table cellspacing="0" cellpadding="0" border="0">
                              <tr>
                                <td width="400" style="   ">
                                  <table width="100%" cellspacing="0" cellpadding="0" border="0">
                                    <tr>
                                      <td width="400">
                                        <table cellspacing="0" cellpadding="0" border="0">
                                          <tr>
                                            <td style="max-width:400px;text-align:center; ;">
                                              <table cellspacing="0" cellpadding="0" border="0">
                                                <tr>
                                                  <td style="text-align:center;" width="400">
                                                    <div style="line-height:22px">
                                                      <span
                                                        style="color: #16171b;line-height:22px;font-family:Arial, Helvetica, Arial, sans-serif; font-size:16px;text-align:center;">А
                                                        еще у
                                                        нас есть
                                                        закрытый
                                                      </span>
                                                      <a href="https://t.me/sslpractice" target="_blank"
                                                        rel="noopener noreferrer"><span
                                                          style="color: #163dd7;line-height:22px;font-family:Arial, Helvetica, Arial, sans-serif; font-size:16px;text-decoration: underline;text-align:center;">телеграмм-канал,
                                                        </span></a>
                                                      <span
                                                        style="color: #000000;line-height:22px;font-family:Arial, Helvetica, Arial, sans-serif; font-size:16px;text-align:center;">где
                                                        регулярно
                                                        выходят
                                                        разборы
                                                        кейсов и
                                                        другая
                                                        полезная
                                                        информация
                                                        -
                                                        подписывайтесь</span>
                                                    </div>
                                                  </td>
                                                </tr>
                                              </table>
                                            </td>
                                          </tr>
                                        </table>
                                      </td>
                                    </tr>
                                  </table>
                                </td>
                              </tr>
                            </table>
                          </td>
                        </tr>
           </table>
           <div style="height:40px;line-height:40px;font-size:40px;width:288px">&nbsp;</div>
          </td>
         </tr>
        </table>
       </td>
      </tr><!-- <![endif]-->
     </table>
    </td>
   </tr>
  </table>
 </div>
</body>

</html>                
                
                
                
                
                """,
                "Спасибо за регистрацию",
            )
            u_s = UserSubscription.objects.create(user=user, subscription=sub, type=2)
            try:
                payload = u_s.pay(period=request.data["period"])
                return Response(
                    {"exist": False, "payload": payload}, status=status.HTTP_200_OK
                )
            except ValueError as error:
                return Response(
                    {"detail": str(error)}, status=status.HTTP_400_BAD_REQUEST
                )

        else:
            return Response("Ошибка токена", status=status.HTTP_401_UNAUTHORIZED)


class ExternalTrialRegistrationCheck(APIView):
    def post(self, request):
        if (
            "token" in request.data
            and request.data["token"] == "askjdlkajldsadk01890923"
        ):
            payment = None
            if isinstance(request.data.get("id"), int):
                payment = Payment.objects.filter(pk=request.data["id"]).first()
            else:
                payment = Payment.objects.filter(payment_id=request.data["id"]).first()
            if payment is None:
                return Response("Нет такого id", status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response(
                    {"status": payment.status}, status=status.HTTP_400_BAD_REQUEST
                )
        else:
            return Response("Ошибка токена", status=status.HTTP_401_UNAUTHORIZED)


class AdminsViewSet(viewsets.GenericViewSet, mixins.CreateModelMixin):
    serializer_class = AdminUserSerializer

    def get_queryset(self):
        return User.objects.filter(is_admin_user=True)


class AdminUsersViewSet(AdminApplicationViewSet):
    permission_classes = [UsersPermissions]
    serializer_class = UserStatisticSerializer

    @action(detail=False, methods=["GET"])
    def export_main(self, request, *args, **kwargs):
        if not "simulator" in self.params:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        simulator = Simulator.objects.get(id=self.params["simulator"])
        sim_users = SimulatorUser.objects.filter(simulator=simulator)
        lesson_users = UserLessonProgress.objects.filter(lesson__simulator=simulator)
        users = []
        for s_user in sim_users:
            user = s_user.user
            user_info = {
                "email": user.email,
                "character": bool(user.avatar),
                "date_register": user.creation_time,
            }
            for l_user in lesson_users.filter(user=user):
                user_info[f"start_{l_user.lesson.name}"] = bool(l_user.pages)
                user_info[f"finish_{l_user.lesson.name}"] = l_user.completed
            users.append(user_info)

        return Response(users)

    @action(detail=False, methods=["GET"])
    def balance(self, request, *args, **kwargs):
        return Response({"balance": request.user.balance})

    @action(detail=False, methods=["GET"])
    def export_score(self, request, *args, **kwargs):
        if not "simulator" in self.params:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        simulator = Simulator.objects.get(id=self.params["simulator"])
        sim_users = SimulatorUser.objects.filter(simulator=simulator)
        places = PlaceUser.objects.filter(
            Q(place__next_places__isnull=True)
            & Q(place__page__lesson__simulator=simulator)
        )

        users = []

        places = [
            427,
            428,
            432,
            444,
            445,
            443,
            441,
            440,
            439,
            437,
            430,
            438,
            423,
            424,
            425,
            450,
            449,
            448,
            447,
            446,
            455,
            454,
            453,
            452,
            451,
            463,
            461,
            459,
            457,
        ]
        p_users = PlaceUser.objects.filter(place__id__in=places)
        for s_user in sim_users:
            user = s_user.user
            user_info = {"email": user.email}
            ps_user = p_users.filter(user=user)
            for place_user in ps_user:
                score = ""
                if place_user.answers != None:
                    answer = int(place_user.answers)
                    u_answer = place_user.place.answers[answer]
                    if u_answer:
                        score += u_answer["text"]
                user_info[f"{place_user.place.page.lesson.name}"] = score
            users.append(user_info)

        return Response(users)

    @action(detail=True, methods=["POST"])
    def active_simulator(self, request, *args, **kwargs):
        if not "active" in request.data:
            return Response(
                {"active": "Это обязательно"}, status=status.HTTP_400_BAD_REQUEST
            )

        if not "simulator" in request.data:
            return Response(
                {"simulator": "Это обязательно"}, status=status.HTTP_400_BAD_REQUEST
            )

        sim_user = SimulatorUser.objects.filter(
            user=self.get_object(), simulator__id=request.data["simulator"]
        ).first()
        sim_user.simulator_paid = request.data["active"]
        sim_user.save()
        return Response()

    def get_queryset(self):
        queryset = []
        if "simulator" in self.params:
            queryset = SimulatorUser.objects.filter(
                simulator=self.params.get("simulator")
            )
        if self.action == "active_simulator":
            queryset = User.objects.all()
        return queryset


class UsersViewSet(
    viewsets.GenericViewSet, mixins.CreateModelMixin, mixins.UpdateModelMixin
):
    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        return UserInfoSerializer

    def get_queryset(self):
        return User.objects.filter(id_admin_user=False)

    def get_object(self):
        return self.request.user

    @action(detail=False, methods=["GET"])
    def details(self, request, *args, **kwargs):
        if request.user.is_anonymous:
            return Response(
                {"details": "Учетные данные не предоставлены"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        companyEmail = CompanyEmails.objects.filter(
            email__iexact=request.user.email
        ).first()
        subscription = UserSubscription.objects.get(user=request.user)
        if companyEmail is None:
            if request.user.company is not None:
                request.user.company = None
                request.user.save()
                subscription.type = 2
                subscription.valid_until = None
                subscription.save()
        else:
            if request.user.company is None:
                request.user.company = companyEmail.company
                request.user.save()
                subscription.type = 6
                subscription.subscription_id = 14
                subscription.valid_until = datetime.now(timezone.utc) + timedelta(
                    days=3650
                )
                subscription.save()

        return Response(self.get_serializer(request.user).data)

    @action(detail=False, methods=["PUT"])
    def signup(self, request, *args, **kwargs):
        if request.user.is_anonymous:
            return Response(
                {"details": "Учетные данные не предоставлены"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        request.user.set_password(request.data["password"])
        request.user.save()

        content = copy(request.data)
        content["user"] = request.user
        try:
            updated_user = auth(content=content, is_login=True)
        except ValueError as error:
            return Response({"detail": str(error)}, status=status.HTTP_400_BAD_REQUEST)

        subscription = UserSubscription.objects.get(user=updated_user)
        subscription.type = 2
        subscription.save()

        if "avatar" in request.FILES:
            updated_user.avatar = request.FILES.get("avatar")
            updated_user.save()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["PUT", "PATCH"])
    def edit(self, request, *args, **kwargs):
        if request.user.is_anonymous:
            return Response(
                {"details": "Учетные данные не предоставлены"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        subscriptions = UserSubscription.objects.filter(user=request.user)
        if subscriptions.exists():
            user_subscription = subscriptions.first()

            if "filled" in request.data:
                if request.data["filled"] == "true":
                    user_subscription.type = 1
                else:
                    user_subscription.type = 0
            elif "subscription_id" in request.data:
                subscription = get_object_or_404(
                    Subscription, id=request.data["subscription_id"]
                )
                user_subscription.subscription = subscription

            user_subscription.save()
        else:
            return Response(
                {"details": "Учетные данные не предоставлены"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        kwargs["partial"] = True
        return super(UsersViewSet, self).update(request, *args, **kwargs)

    @action(detail=False, methods=["POST"])
    def change_password(self, request, *args, **kwargs):
        try:
            password_validation.validate_password(request.data["password"])
        except ValidationError as error:
            return Response({"detail": str(error)}, status.HTTP_400_BAD_REQUEST)

        if request.user.is_anonymous:
            user = get_object_or_404(User, temporary_code=request.data["key"])
            user.temporary_code = None
        else:
            user = request.user

        user.set_password(request.data["password"])
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["POST"])
    def reset_password_2(self, request, *args, **kwargs):

        user = get_object_or_404(User, temporary_code=request.data["key"])
        user.temporary_code = None

        user.set_password(request.data["password"])
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["POST"])
    def reset_password(self, request, *args, **kwargs):
        user = User.objects.filter(email=request.data["email"]).first()
        if user is None:
            return Response(
                {"detail": "Нет такого пользователя"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.temporary_code = rand_slug()
        user.save()
        confirmation_link = "https://skillslab.center/reset/{key}".format(
            key=user.temporary_code
        )
        send_email(
            user.email,
            """Для восстановления пароля перейдите по <a href={confirmation_link}>ссылке</a>
            <br><br>
            Ссылка действительна в течение 24 часов.""".format(
                confirmation_link=confirmation_link
            ),
            "Восстановление пароля",
        )

        return Response(status=status.HTTP_204_NO_CONTENT)


class AuthAttemptViewSet(viewsets.ModelViewSet):
    queryset = AuthAttempt.objects.all()
    serializer_class = AuthAttemptSerializer

    @action(detail=False, methods=["post"], url_path="token")
    def token(self, request):
        code = request.data["code"]

        user = User.objects.get(temporary_code=code)
        user.temporary_code = None
        user.save()

        attempt_auth = AuthAttempt.objects.filter(code=code).first()
        if attempt_auth:
            attempt_auth.code = None
            attempt_auth.save()

        instance, token = AuthToken.objects.create(user=user, expiry=None)

        subscriptions = UserSubscription.objects.filter(user=user)
        if subscriptions.exists():
            auto_user = True
        else:
            auto_user = False

        return Response(
            {
                "token": token,
                "email": user.email,
                "full_name": f"{user.first_name} {user.last_name}",
                "admin": user.is_superuser,
                "auto_user": auto_user,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["get"], url_path="oauth/init")
    def social_init(self, request):
        provider = request.GET.get("provider")
        simulator = request.simulator
        redirect_uri = HOST_URL + "/api/auth/v2/oauth/login/"

        auth_attempt = AuthAttempt(simulator=simulator)
        auth_attempt.save()

        if provider == "facebook":
            url = (
                "https://www.facebook.com/v11.0/dialog/oauth?"
                f"client_id={simulator.group.auth_facebook_key}"
                f"&redirect_uri={redirect_uri + 'facebook/'}"
                f"&state={auth_attempt.id}"
                # "&scope=email"
            )
        elif provider == "vk":
            url = (
                "https://oauth.vk.com/authorize?"
                f"client_id={simulator.group.auth_vk_key}"
                f"&redirect_uri={redirect_uri + 'vk/'}"
                f"&state={auth_attempt.id}"
                f"&scope=email"
                "&response_type=code"
            )
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        return Response({"url": url, "attemptID": auth_attempt.id})

    @action(
        detail=False,
        methods=["get"],
        url_path="oauth/login/facebook",
        renderer_classes=[StaticHTMLRenderer],
    )
    def social_login_facebook(self, request):
        state = request.GET.get("state")
        auth_attempt = AuthAttempt.objects.get(id=int(state))
        simulator = auth_attempt.simulator

        client_error_url = (
            HOST_URL
            + "/api/auth/v2/oauth/init/?provider=facebook&simulator={}".format(
                simulator.id
            )
        )
        redirect_uri = HOST_URL + "/api/auth/v2/oauth/login/facebook/"

        if "error" in request.GET:
            auth_attempt.status = 2
            auth_attempt.save()
            return Response("<html><body>Отмена авторизации...</body></html>")

        code = request.GET.get("code")

        # Обмен кода на маркер доступа клиента
        url = (
            "https://graph.facebook.com/v11.0/oauth/access_token?"
            f"client_id={simulator.group.auth_facebook_key}"
            f"&client_secret={simulator.group.auth_facebook_secret}"
            f"&redirect_uri={redirect_uri}"
            f"&code={code}"
        )
        response = requests.get(url)

        if not response.status_code == 200:
            return HttpResponseRedirect(client_error_url)

        input_token = json.loads(response.text)["access_token"]

        # Генерирование маркера доступа приложения
        url = (
            "https://graph.facebook.com/oauth/access_token?"
            f"client_id={simulator.group.auth_facebook_key}"
            f"&client_secret={simulator.group.auth_facebook_secret}"
            "&grant_type=client_credentials"
        )
        response = requests.get(url)

        if not response.status_code == 200:
            auth_attempt.status = 1
            auth_attempt.save()
            return Response("<html><body>Ошибка авторизации!</body></html>")

        access_token = json.loads(response.text)["access_token"]

        # Проверка маркера доступа клиента
        url = (
            "https://graph.facebook.com/debug_token?"
            f"input_token={input_token}"
            f"&access_token={access_token}"
        )
        response = requests.get(url)

        if not response.status_code == 200:
            return HttpResponseRedirect(client_error_url)

        user_id = json.loads(response.text)["data"]["user_id"]

        # Получение данных клиента
        url = f"https://graph.facebook.com/{user_id}?" f"access_token={input_token}"
        response = requests.get(url)

        if not response.status_code == 200:
            return HttpResponseRedirect(client_error_url)

        content = json.loads(response.text)
        print(content)  # TODO get email
        content["user_id"] = content["id"]
        content["simulator"] = simulator.id

        try:
            authorized_user = auth(
                content=content,
                check_login=True,
                backend="facebook",
                need_temporary_code=True,
            )
        except:
            auth_attempt.status = 1
            auth_attempt.save()
            return Response("<html><body>Ошибка авторизации!</body></html>")

        auth_attempt.status = 3
        auth_attempt.code = authorized_user.temporary_code
        auth_attempt.user = authorized_user
        auth_attempt.save()
        return Response("<html><body>Выполняем авторизацию...</body></html>")

    @action(
        detail=False,
        methods=["get"],
        url_path="oauth/login/vk",
        renderer_classes=[StaticHTMLRenderer],
    )
    def social_login_vk(self, request):
        state = request.GET.get("state")
        auth_attempt = AuthAttempt.objects.get(id=int(state))
        simulator = auth_attempt.simulator

        client_error_url = (
            HOST_URL
            + "/api/auth/v2/oauth/init/?provider=vk&simulator={}".format(simulator.id)
        )
        redirect_uri = HOST_URL + "/api/auth/v2/oauth/login/vk/"

        if "error" in request.GET:
            auth_attempt.status = 2
            auth_attempt.save()
            return Response("<html><body>Отмена авторизации...</body></html>")

        code = request.GET.get("code")

        # Обмен кода на токен пользователя
        url = (
            "https://oauth.vk.com/access_token?"
            f"client_id={simulator.group.auth_vk_key}"
            f"&client_secret={simulator.group.auth_vk_secret}"
            f"&redirect_uri={redirect_uri}"
            f"&code={code}"
        )

        response = requests.get(url)

        if not response.status_code == 200:
            return HttpResponseRedirect(client_error_url)

        content = json.loads(response.text)
        content["simulator"] = simulator.id

        try:
            authorized_user = auth(
                content=content,
                check_login=True,
                backend="vk",
                need_temporary_code=True,
            )
        except:
            auth_attempt.status = 1
            auth_attempt.save()
            return Response("<html><body>Ошибка авторизации!</body></html>")

        auth_attempt.status = 3
        auth_attempt.code = authorized_user.temporary_code
        auth_attempt.user = authorized_user
        auth_attempt.save()
        return Response("<html><body>Выполняем авторизацию...</body></html>")
