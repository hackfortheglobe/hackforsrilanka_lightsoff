from django.urls import path
from lightsoff import views

urlpatterns = [path("test/", views.SendTestEmail.as_view())]
