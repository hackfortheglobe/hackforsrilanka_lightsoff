import datetime
from conf.celery import app
from django.core.mail import send_mail
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
import dateutil.parser
from .models import *

# from lightsoff.models import GROUP_CHOICES, Subscriber
from lightsoff.utils import (
    commit_response_to_db_or_false,
    get_schedule_date,
    send_mass_notification,
    login_sms_api
)

import requests
import json
from requests.structures import CaseInsensitiveDict
from django_celery_beat.models import (
                                       PeriodicTask,
                                       ClockedSchedule,
                                       CrontabSchedule)
from django.db.models import Prefetch
from django.core.paginator import Paginator
from django.db.models import F



# @app.task()
# def send_confirmation_email(email):
#     """Asynchronously sends a confirmation email to the user after sign up.
#     Have to run by callying send_confirmation_email.delay()
#     """
#     send_mail(
#         "LightsOff Subscription Confirmation",
#         "You have been subscribed to the Lightsoff newsletter.",
#         from_email=None,
#         recipient_list=[email],
#     )


# @app.task()
# def send_update_emails():
#     """Periodic task to pull updates from the API for the next day.

#     Nothing is done if there are no updates or if we have already acted
#     upon the update in a previous run of this task. It checks the MD5 hash
#     of the JSON output to determine this.

#     Dates are provided in ISO 8601 format by the API endpoint. We convert
#     them to local time, which is defined as Asia/Colombo by the TZ variable in
#     the conf/settings.py file.

#     TODO: Also send updates about upcoming days if the schedule is available.
#     """
#     for group, _ in GROUP_CHOICES:
#         data = Subscriber.objects.filter(group=group).values_list(
#             "email", "unsubscribe_token"
#         )
#         emails = [email for email, _ in data]
#         unsubscribe_tokens = [token for _, token in data]

#         # Skip if there are no subscribers
#         if len(emails) == 0:
#             continue

#         tomorrow_date = timezone.localdate() + datetime.timedelta(days=1)
#         schedule = get_schedule_date(group, tomorrow_date)

#         # Skip if we have already acted upon this schedule update
#         if not commit_response_to_db_or_false(schedule, group, tomorrow_date):
#             continue

#         # Skip if there are no power cuts
#         if len(schedule) == 0:
#             continue

#         # Create list of human readable strings of the time windows of the cutoffs
#         schedule_text = []
#         for row in schedule:
#             raw_start_time = dateutil.parser.isoparse(row["starting_period"])
#             raw_end_time = dateutil.parser.isoparse(row["ending_period"])

#             # Convert to local time (Asia / Colombo)
#             start_time = timezone.make_aware(
#                 timezone.make_naive(raw_start_time), timezone.get_current_timezone()
#             )
#             end_time = timezone.make_aware(
#                 timezone.make_naive(raw_end_time), timezone.get_current_timezone()
#             )
#             string = (
#                 f"{start_time.strftime('%I:%M %p')} - {end_time.strftime('%I:%M %p')}"
#             )
#             schedule_text.append(string)

#         tomorrow_date_readable = tomorrow_date.strftime("%d-%m-%Y")
#         send_mass_notification(
#             emails, unsubscribe_tokens, group, tomorrow_date_readable, schedule_text
#         )



@app.task(bind=True)
def send_sms_notification(self):
    url = "https://e-sms.dialog.lk/api/v1/sms"
    headers = CaseInsensitiveDict()
    access_token = login_sms_api()
    headers["Authorization"] = f"Bearer {access_token}"
    headers["Content-Type"] = "application/json"
    schedule_group = ScheduleGroup.objects.filter(is_run=False)
    for schedule_data in schedule_group:
        all_sub = Subscriber.objects.filter(group_name=schedule_data.group_name,
                                            is_unsubscribed=False)
        paginator = Paginator(all_sub, 100)
        for page_no in paginator.page_range:
            current_page = paginator.get_page(page_no)
            current_qs = current_page.object_list
            tx_id = Transaction.objects.all().order_by('-id').first()
            message = f"There will be a scheduled power cutoff for group {schedule_data.group_name},from {schedule_data.starting_period} to {schedule_data.ending_period}."
            numbers = list(current_qs.values(mobile=F("mobile_number")))
            resp = send_sms(numbers, message, tx_id.id)
            if resp.status_code == 200:
                res_data = resp.json()
                tx_data = Transaction.objects.create(campaingn_id=res_data["data"].get("campaignId", None),
                                           campaingn_cost=res_data["data"].get("campaignCost", None),
                                           user_id=res_data["data"].get("userId", None),
                                           status="SUCCESS")
                batch_data = Batch.objects.create(transaction=tx_data,
                                    status="SUCCESS",
                                    message=message,
                                    schedule=schedule_data)
                batch_data.subscriber.set(list(current_qs.values_list("id", flat=True)))
                batch_data.save()
            else:
                res_data = resp.json()
                tx_data = Transaction.objects.create(status="FAILED")
                batch_data = Batch.objects.create(transaction=tx_data,
                                    status="FAILED",
                                    message=message,
                                    schedule=schedule_data)
                batch_data.subscriber.set(list(current_qs.values_list("id", flat=True)))
                batch_data.save()
                time = datetime.datetime.now(tz=timezone.utc) + timedelta(minutes=5)
                clock_time = ClockedSchedule.objects.create(clocked_time=time)
                PeriodicTask.objects.create(crontab=clock_time,
                                            task="lightsoff.tasks.send_sms_to_batch",
                                            name=f'send_batch_sms_{batch_data.id}')
            schedule_data.is_run = True
            schedule_data.save()

@app.task(bind=True, max_retries=settings.CELERY_TASK_PUBLISH_RETRY)
def send_sms_to_batch(self):
    url = "https://e-sms.dialog.lk/api/v1/sms"
    headers = CaseInsensitiveDict()
    access_token = login_sms_api()
    headers["Authorization"] = f"Bearer {access_token}"
    headers["Content-Type"] = "application/json"
    batch_data = Batch.objects.filter(status="FAILED"
                                      ).prefetch_related(
                                          Prefetch("subscriber",
                                                queryset=Subscriber.objects.filter(is_unsubscribed=False)
                                                            )
                                                        )
    tx_id = Transaction.objects.all().order_by('-id').first()
    message = f"There will be a scheduled power cutoff for group {batch_data.schedule.group_name},from {batch_data.schedule.starting_period} to {batch_data.schedule.ending_period}."
    numbers = list(current_qs.values(mobile=F("mobile_number")))
    resp = send_sms(numbers, message, tx_id.id)
    if resp.status_code == 200:
        tx_data = Transaction.objects.create(campaingn_id=res_data["data"].get("campaignId", None),
                                   campaingn_cost=res_data["data"].get("campaignCost", None),
                                   user_id=res_data["data"].get("userId", None),
                                   status="SUCCESS")
        batch_data.transaction = tx_data
        batch_data.status = "SUCCESS"
        batch_data.save()
        print("SUCCESS")
    else:
        tx_data = Transaction.objects.create(status="FAILED")
        batch_data.transaction = tx_data
        batch_data.status = "FAILED"
        batch_data.save()
        print("FAILED")
        raise self.retry(countdown=300)

