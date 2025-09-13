"""backend URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from notifications.views import NotificationViewSet
from statistics.views import AdminStatisticViewSet
from theories.views import AdminTheoryChapterViewSet, TheoryChapterViewSet
from characters.views import AdminCharacterViewSet
from django.conf.urls.static import static
from django.conf import settings
from utils.veiws import UploadImage
from places.views import AdminPlaceViewSet, PlaceViewSet
from pages.views import AdminPageViewSet, PageViewSet
from lessons.views import AdminLessonViewSet, LessonViewSet
from notebook.views import GetNotebook, GetNote
from django.contrib import admin
from django.urls import path
from django.urls.conf import include
from backend.auth_token import AuthToken
from rest_framework_nested import routers
from simulator_groups.views import AdminSimulatorGroupViewSet
from teachers.views import GetTeachers, GetTeacher, ChooseTeacher
from club.views import GetClubs, GetRating, GetPlayers, GetTournament, GetRatingPK
from simulators.views import AdminSimulatorViewSet, SimulatorViewSet
from user_profile.views import (
    AdminUsersViewSet,
    AdminsViewSet,
    UsersViewSet,
    AuthAttemptViewSet,
    ExternalTrialRegistration,
    ExternalTrialRegistrationCheck,
    CheckEmailSub,
)
from bot.views import Bot, BotAdmin, TrainerBot, AIBot
from payments.views import AdminPromoCodeViewSet, PaymentViewSet
from emails.views import AdminEmailViewSet
from comment_requests.views import AdminCommentRequestViewSet, CommentRequestViewSet
from products.views import AdminProductsViewSet, ProductsViewSet
from external_api.views import ExternalSimulatorsViewSet, ExternalAuthAttemptViewSet
from tags.views import AdminTagsViewSet, TagsViewSet
from banners.views import AdminBannersViewSet, BannersViewSet
from subscriptions.views import AdminSubscriptionViewSet, SubscriptionViewSet
from recommendations.views import AdminRecommendationViewSet, RecommendationViewSet
from poll.views import PollBot
from test.views import GetMainData
from course.views import GetCoursesData, GetCourse, GetHomeCourses
from company.views import (
    GetCompanyEmails,
    CompanyEmail,
    CompanyView,
    GetCompanyStat,
    GetCompanyUserStat,
    GetCompanyUserPage,
)
from ext_course.views import CreateClient, SendToTG, PaymentNotificaiton
from feedback.views import GetFeedback
from decomposition.views import GetDecomposition

router_admin = routers.DefaultRouter()

router_admin.register(r"simulator_groups", AdminSimulatorGroupViewSet, "SimulatorGroup")
router_admin.register(r"simulators", AdminSimulatorViewSet, "Simulator")
router_admin.register(r"lessons", AdminLessonViewSet, "Lessons")
router_admin.register(r"pages", AdminPageViewSet, "Pages")
router_admin.register(r"places", AdminPlaceViewSet, "Places")
router_admin.register(r"admins", AdminsViewSet, "Admins")
router_admin.register(r"users", AdminUsersViewSet, "Users")
router_admin.register(r"characters", AdminCharacterViewSet, "Characters")
router_admin.register(r"theory_chapters", AdminTheoryChapterViewSet, "TheoryChapters")
router_admin.register(r"promo_codes", AdminPromoCodeViewSet, "PromoCodes")
router_admin.register(r"emails", AdminEmailViewSet, "Emails")
router_admin.register(r"comment_requests", AdminCommentRequestViewSet, "CommentRequest")
router_admin.register(r"products", AdminProductsViewSet, "Products")
router_admin.register(r"statistics", AdminStatisticViewSet, "Statistics")
router_admin.register(r"tags", AdminTagsViewSet, "Tags")
router_admin.register(r"banners", AdminBannersViewSet, "Banners")
router_admin.register(r"subscriptions", AdminSubscriptionViewSet, "Subscriptions")
router_admin.register(r"recommendations", AdminRecommendationViewSet, "Recommendations")

router_user = routers.DefaultRouter()

router_user.register(r"users", UsersViewSet, "Users")
router_user.register(r"auth/v2", AuthAttemptViewSet, "Auth")
router_user.register(r"simulators", SimulatorViewSet, "Simulators")
router_user.register(r"lessons", LessonViewSet, "Lessons")
router_user.register(r"pages", PageViewSet, "Pages")
router_user.register(r"places", PlaceViewSet, "Places")
router_user.register(r"payments", PaymentViewSet, "Payments")
router_user.register(r"comment_requests", CommentRequestViewSet, "CommentRequest")
router_user.register(r"notifications", NotificationViewSet, "Notification")
router_user.register(r"theories", TheoryChapterViewSet, "Theories")
router_user.register(r"products", ProductsViewSet, "Products")
router_user.register(r"tags", TagsViewSet, "Tags")
router_user.register(r"banners", BannersViewSet, "Banners")
router_user.register(r"subscriptions", SubscriptionViewSet, "Subscriptions")
router_user.register(r"recommendations", RecommendationViewSet, "Recommendations")

router_external = routers.DefaultRouter()

router_external.register(r"auth", ExternalAuthAttemptViewSet, "Auth")
router_external.register(r"simulators", ExternalSimulatorsViewSet, "Simulators")


urlpatterns = (
    [
        path("summernote/", include("django_summernote.urls")),
        path("api_admin/", include(router_admin.urls)),
        path("api/", include(router_user.urls)),
        path("external_api/", include(router_external.urls)),
        path("admin/", admin.site.urls),
        path("api/auth/", AuthToken.as_view()),
        path("api/teachers/", GetTeachers.as_view(), name="GetTeachers"),
        path("api/teacher/", GetTeacher.as_view(), name="GetTeacher"),
        path("api/notebook/all/", GetNotebook.as_view(), name="GetNotebook"),
        path("api/notebook/get/", GetNote.as_view(), name="GetNote"),
        path("api/clubs/", GetClubs.as_view(), name="GetClubs"),
        path("api/clubs/rating/", GetRating.as_view(), name="GetRating"),
        path("api/clubs/rating/<int:id>/", GetRatingPK.as_view(), name="GetRatingPK"),
        path("api/clubs/tournament/", GetTournament.as_view(), name="GetTournament"),
        path("api/clubs/players/", GetPlayers.as_view(), name="GetPlayers"),
        path("api/teacher/choose/", ChooseTeacher.as_view(), name="ChooseTeacher"),
        path("api/bot/main/", Bot.as_view(), name="Bot"),
        path("api/bot/admin/", BotAdmin.as_view(), name="BotAdmin"),
        path("api/bot/ai/", AIBot.as_view(), name="AIBot"),
        path("api/bot/trainer/", TrainerBot.as_view(), name="TrainerBot"),
        # path('api/bot/temp/', Temp.as_view(), name='BotAdmin'),
        path("api_admin/auth/", AuthToken.as_view()),
        path("api_admin/upload_image/", UploadImage.as_view()),
        path("api/upload_image/", UploadImage.as_view()),
        path("api/external/create_user/", ExternalTrialRegistration.as_view()),
        path(
            "api/external/create_user/check/", ExternalTrialRegistrationCheck.as_view()
        ),
        path("api/tests/main_data/", GetMainData.as_view()),
        path("api/polls/bot/", PollBot.as_view()),
        path("api/courses/", GetCoursesData.as_view()),
        path("api/courses/all/", GetHomeCourses.as_view()),
        path("api/course/", GetCourse.as_view()),
        path("api/company/emails/", GetCompanyEmails.as_view()),
        path("api/company/emails/<int:id>/", CompanyEmail.as_view()),
        path("api/company/data/<str:slug>/", CompanyView.as_view()),
        path("api/company/stat/", GetCompanyStat.as_view()),
        path("api/company/user/", GetCompanyUserStat.as_view()),
        path("api/company/user/page/", GetCompanyUserPage.as_view()),
        path("api/ext_course/create/<int:id>/", CreateClient.as_view()),
        path("api/ext_course/payment/notification/", PaymentNotificaiton.as_view()),
        path("api/ext_course/sendtotg/", SendToTG.as_view()),
        path("api/ext_api/usercheck/", CheckEmailSub.as_view()),
        path("api/feedback/", GetFeedback.as_view()),
        path("api/decomposition/", GetDecomposition.as_view()),
    ]
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
)
