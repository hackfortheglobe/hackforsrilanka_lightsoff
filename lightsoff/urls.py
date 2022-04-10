from argparse import Namespace
from django.urls import path
from lightsoff import views


app_name = "lightsoff"
urlpatterns = [
    path("", views.subscribe, name="subscribe"),
    path("unsubscribe/", views.unsubscribe, name="unsubscribe"),
    path("force-notify/", views.force_notify, name="force-notify"),
]
