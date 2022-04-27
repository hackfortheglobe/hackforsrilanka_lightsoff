from argparse import Namespace
from django.urls import path
from lightsoff import views
from .api.apis import *

app_name = "lightsoff"
urlpatterns = [
    path("", views.subscribe, name="subscribe"),
    path("unsubscribe/", views.unsubscribe, name="unsubscribe"),
    path("force-notify/", views.force_notify, name="force-notify"),
    path("send-sms/", views.send_sms_to_user, name="send_sms"),
    path("api/create-schedule/", CreateSchedule.as_view(), name="create_schedule"),
    path("api/schedule-data/", GetAllPublicSchedule.as_view(), name="schedule_data"),
    path("api/power-schedule/<str:group>/", SchedulesByGroup.as_view(), name="power_schedule"),
]

