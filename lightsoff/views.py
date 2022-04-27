from django.shortcuts import render
# from lightsoff.forms import SubscribeForm
from django.http import HttpResponse
from lightsoff.tasks import send_confirmation_email, send_update_emails
# from lightsoff.models import Subscriber
from django.contrib.admin.views.decorators import staff_member_required
from .models import SmsApiAccessToken

def subscribe(request):
    """Main view for users to subscribe to notifications"""
    if request.method == "POST":
        form = SubscribeForm(request.POST)
        if form.is_valid():
            form.save()
            send_confirmation_email.delay(form.cleaned_data["email"])
            return render(request, "lightsoff/subscribe_success.html")
    else:
        form = SubscribeForm()

    return render(request, "lightsoff/subscribe.html", {"form": form})


def unsubscribe(request):
    """View for users to unsubscribe from notifications.

    Each user has an associated unique token that is
    generated upon sign up. This prevents malicious users from
    unsubscribing users if, for instance, we an email as an input
    to this view.

    Returns an invalid request message if token does not exist or
    if it has not been provided.
    """
    if request.method == "GET" and request.GET.get("token"):
        token = request.GET.get("token")
        try:
            subscriber = Subscriber.objects.get(unsubscribe_token=token)
            subscriber.delete()
            return render(
                request,
                "lightsoff/message.html",
                context={"message": "You have been unsubscribed."},
            )
        except Subscriber.DoesNotExist:
            pass
    return render(
        request,
        "lightsoff/message.html",
        context={"message": "Invalid request."},
    )


@staff_member_required()
def force_notify(request):
    """For administrator use only. Allows you to force
    a pull from the API and send notifications to all subscribers.
    """
    send_update_emails.delay()
    return render(
        request,
        "lightsoff/message.html",
        context={"message": "Notification task to all subscribers has been queued."},
    )


def update(request):
    """TODO: Implement a page where subscribers can update their group"""
    return NotImplementedError()


def report(request):
    """TODO: Implement a page where users can report power shutoff deviations
    from the official schedule. Main purpose is for data collection, and maybe
    prediction."""
    return render(request, "lightsoff/report.html")

import requests
import json
from requests.structures import CaseInsensitiveDict
def send_sms_to_user(request):
    url = "https://e-sms.dialog.lk/api/v1/sms/check-transaction"

    headers = CaseInsensitiveDict()
    headers["Authorization"] = "Bearer yJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6ODUxMCwidXNlcm5hbWUiOiJoYWNrNGdsb2JlIiwibW9iaWxlIjo3NzM2MzQ0MTAsImVtYWlsIjoibmlzaGFud0BnbWFpbC5jb20iLCJpYXQiOjE2NTA5NjUwNjksImV4cCI6MTY1MTAwODI2OX0.DSK6Db2ECNZpZ4BfvZyfyjWJY40f6k6pQ0vM2oREvZQ"
    # headers["Content-Type"] = "application/json" +94773634410

    data = {
            "transaction_id":"15",
            }
    resp = requests.post(url, headers=headers, data=data)
    res_data = resp.json()
    if resp.status_code != 200:
        if res_data.get("status", "") == "failed":
            campaingnId = res_data["data"].get("campaignId", None)
    else:
        res_data.get("errCode")
    print(resp.status_code)
    print(resp)
    print(resp.json())
    print("END###########")
    
