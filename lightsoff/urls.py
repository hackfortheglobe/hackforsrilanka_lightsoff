from django.urls import path
from lightsoff import views
from .api.apis import *

app_name = "lightsoff"
urlpatterns = [
    path("api/unsubscribe/", Unsubscribed.as_view(), name="unsubscribe"),
    path("api/subscribe/", UserSubscription.as_view(), name="subscribe"),
    path("api/change-group/", ChangeSubscriberGroup.as_view(), name="change_group"),
    path("api/verify-otp/", VerifyOtp.as_view(), name="verify_otp"),
    path("api/create-schedule/", CreateSchedule.as_view(), name="create_schedule"),
    path("api/schedule-data/", GetAllPublicSchedule.as_view(), name="schedule_data"),
    path("api/power-schedule/<str:group>/", SchedulesByGroup.as_view(), name="power_schedule"),
    path("api/schedule-by-place/", SearchSchedulesByPlace.as_view(), name="schedule_by_place"),
    path("api/search-by-district/", SearchByDistrict.as_view(), name="search_by_district"),
    path("api/all-group/", AllGroupName.as_view(), name="all_group"),
    path("api/all-gss/", AllGCCName.as_view(), name="all_gss"),
    path("api/all-area/", AllAreaName.as_view(), name="all_area"),
    path("api/create-place/", PlaceView.as_view(), name="create_place"),
    path("api/subscribed-user/", GetAllSubscribedUser.as_view(), name="subscribed_user"),
    path("api/all-district/", GetAllDistrict.as_view(), name="all_district"),
]

