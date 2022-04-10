from django.shortcuts import render
from lightsoff.forms import SubscribeForm
from django.http import HttpResponse
from lightsoff.tasks import send_confirmation_email, send_update_emails
from lightsoff.models import Subscriber


def subscribe(request):
    if request.method == "POST":
        form = SubscribeForm(request.POST)
        if form.is_valid():
            form.save()
            send_confirmation_email.delay(form.cleaned_data["email"])
            return render(request, "lightsoff/subscribe_success.html")
    else:
        form = SubscribeForm()

    return render(request, "lightsoff/subscribe.html", {"form": form})


def update(request):
    return render(request, "lightsoff/update.html")


def report(request):
    return render(request, "lightsoff/report.html")


def unsubscribe(request):
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


def force_notify(request):
    send_update_emails.delay()
    return HttpResponse("Update emails sent.")
