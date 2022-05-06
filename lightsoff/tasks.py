import datetime
from conf.celery import app
from django.core.mail import send_mail
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
import dateutil.parser
from .models import *

# from lightsoff.models import GROUP_CHOICES, Subscriber
from lightsoff.utils import *

import requests
import json
from requests.structures import CaseInsensitiveDict
from django_celery_beat.models import (PeriodicTask,
                                       ClockedSchedule)
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



@app.task(bind=True, max_retries=0)
def send_sms_notification(self):

    link = f"https://ekata.lk/unsubscribe"
    url = "https://e-sms.dialog.lk/api/v1/sms"
    headers = CaseInsensitiveDict()
    access_token = login_sms_api()
    headers["Authorization"] = f"Bearer {access_token}"
    headers["Content-Type"] = "application/json"
    schedule_group = ScheduleGroup.objects.filter(is_run=False,
                                                  starting_period__gte=datetime.datetime.now(tz=local_time)
                                                  ).select_related()
    for schedule_data in schedule_group:
        all_sub = Subscriber.objects.filter(group_name=schedule_data.group_name,
                                            is_unsubscribed=False)
        if len(all_sub) == 0:
            print(f"there is not subscriber for this group name {schedule_data.group_name.name}")
            continue
        sub_user = all_sub.values(mobile=F("mobile_number"))
        paginator = Paginator(sub_user, 100)
        for page_no in paginator.page_range:
            current_page = paginator.get_page(page_no)
            current_qs = current_page.object_list
            tx_id = generate_uniqe_id()
            from_date = schedule_data.starting_period.strftime('%b %-dth')
            from_time = schedule_data.starting_period.strftime('%I:%S %p')
            to_time = schedule_data.ending_period.strftime('%I:%S %p')
            message = f"{from_date} from {from_time} to {to_time} [Group {schedule_data.group_name.name} power cut schedule].To unsubscribe go to {link}"
            numbers = list(current_qs)
            resp = send_sms(numbers, message, tx_id)
            if resp.status_code == 200:
                res_data = resp.json()
                tx_data = Transaction.objects.create(campaingn_id=res_data["data"].get("campaignId", None),
                                                     campaingn_cost=res_data["data"].get("campaignCost", None),
                                                     user_id=res_data["data"].get("userId", None),
                                                     status="SUCCESS",
                                                     tx_id=tx_id)
                batch_data = Batch.objects.create(transaction=tx_data,
                                                  status="SUCCESS",
                                                  is_batch_run=True,
                                                  message=message,
                                                  schedule=schedule_data)
                batch_data.subscriber.set(list(current_qs.values_list("id", flat=True)))
                batch_data.save()
                print("Batch has been run successfully.")
            else:
                res_data = resp.json()
                tx_data = Transaction.objects.create(status="FAILED",
                                                     tx_id=tx_id)
                batch_data = Batch.objects.create(transaction=tx_data,
                                    status="FAILED",
                                    message=message,
                                    schedule=schedule_data)
                batch_data.subscriber.set(list(current_qs.values_list("id", flat=True)))
                batch_data.save()
                time = datetime.datetime.now(tz=local_time) + timedelta(minutes=5)
                clock_time = ClockedSchedule.objects.create(clocked_time=time)
                PeriodicTask.objects.create(clocked=clock_time,
                                            one_off=True,
                                            task="lightsoff.tasks.send_sms_to_batch",
                                            name=f'send_batch_sms_{batch_data.id}')
                print(f"Task is created for this batch number {batch_data.id}.")
            schedule_data.is_run = True
            schedule_data.save()

@app.task(bind=True, max_retries=settings.CELERY_TASK_PUBLISH_RETRY)
def send_sms_to_batch(self):
    link = f"https://ekata.lk/unsubscribe"
    url = "https://e-sms.dialog.lk/api/v1/sms"
    headers = CaseInsensitiveDict()
    access_token = login_sms_api()
    headers["Authorization"] = f"Bearer {access_token}"
    headers["Content-Type"] = "application/json"
    time = datetime.datetime.now(tz=local_time) + timedelta(minutes=5)
    all_batch_data = Batch.objects.filter(status="FAILED",
                                          is_batch_run=False,
                                          schedule__starting_period__gte=time
                                          ).prefetch_related(
                                            Prefetch("subscriber",
                                                     queryset=Subscriber.objects.filter(is_unsubscribed=False)))
    is_batch_success = True
    for batch_data in all_batch_data:
        ## it will call the api until transaction id is unique.
        if batch_data.is_batch_run:
            continue
        from_date = batch_data.schedule.starting_period.strftime('%b %-dth')
        from_time = batch_data.schedule.starting_period.strftime('%I:%S %p')
        to_time = batch_data.schedule.ending_period.strftime('%I:%S %p')
        count_number = 1
        while True:
            tx_id = generate_uniqe_id()
            message = f"{from_date} from {from_time} to {to_time} [Group {batch_data.schedule.group_name} power cut schedule].To unsubscribe go to {link}"
            numbers = list(batch_data.subscriber.all().values(mobile=F("mobile_number")))
            resp = send_sms(numbers, message, tx_id)
            res_data = resp.json()
            if resp.status_code == 401 and res_data.get("errCode") == 104:
                Transaction.objects.create(status="FAILED",
                                           tx_id=tx_id)
                print("Transaction id already exists.")
            else:
                break;
            if count_number == 899:
                break;
            count_number +=1

        if resp.status_code == 200:
            tx_data = Transaction.objects.create(campaingn_id=res_data["data"].get("campaignId", None),
                                       campaingn_cost=res_data["data"].get("campaignCost", None),
                                       user_id=res_data["data"].get("userId", None),
                                       status="SUCCESS",
                                       tx_id=tx_id)
            batch_data.transaction = tx_data
            batch_data.status = "SUCCESS"
            batch_data.is_batch_run=True
            batch_data.save()
            print(f"Batch number {batch_data.id} has been run successfully.")
        else:
            is_batch_success = False
            tx_data = Transaction.objects.create(status="FAILED",
                                                 tx_id=tx_id)
            batch_data.transaction = tx_data
            batch_data.status = "FAILED"
            batch_data.save()
            print(f"Batch number {batch_data.id} has been failed.")
    if not is_batch_success:
        print("This attempt has been failed.")
        raise self.retry(countdown=300)

from lightsoff.scraper.scraper import scrape
from os.path import exists
from os import getcwd, remove


@app.task(bind=True, max_retries=0)
def scrapper_data(self):
    DOMAIN_NAME = f"https://{settings.DOMAIN_NAME}"
    place_url = f"{DOMAIN_NAME}/api/create-place/"
    schedule_url = f"{DOMAIN_NAME}/api/create-schedule/"
    api_key = settings.LIGHT_OFF_API_KEY
    base_dir = f"{getcwd()}/lightsoff"
    output_dir = f"{base_dir}/scraper/outputs/"
    output_place = f"{base_dir}/scraper/outputs/places.json"
    output_schedule = f"{base_dir}/scraper/outputs/schedules.json"
    output_last_id = f"{base_dir}/scraper/outputs/last_processed_document_id.txt"

    last_obj = LastProcessedDocument.objects.all().last()
    if last_obj:
        scrape(last_obj.last_processed_id)
    else:
        scrape("")
    file_exists = exists(output_last_id)
    if file_exists:
        headers = {}
        headers = CaseInsensitiveDict()
        headers["Content-Type"] = "application/json"
        headers["Authorization"] = f"Api-Key {api_key}"
        with open(output_place) as f:
            place_data = json.load(f)
        place_data = json.dumps(place_data)
        for single_place_data in place_data:
            batch={}
            batch[single_place_data] = place_data[single_place_data]
            requests.post(url=place_url, headers=headers, data=batch)

        ##place_data flushing the data from memory
        place_data = None
        with open(output_schedule) as f:
            schedule_data = json.load(f)
        schedule_data = json.dumps(schedule_data)
        schedule_batches = chunks(schedule_data['schedules'], 10)
        for schedule_batch in schedule_batches:
            batch={}
            batch['schedules'] = schedule_batch
            requests.post(url=schedule_url, headers=headers, data=batch)
        
        ##schedule_data flushing the data from memory
        schedule_data = None
        with open(output_last_id) as f:
            last_processed_id = f.read()
        if last_obj:
            last_obj.last_processed_id = last_processed_id
            last_obj.save()
        else:
            LastProcessedDocument.objects.create(last_processed_id=last_processed_id)
        ##last_processed_id flushing the data from memory
        last_processed_id = None
        remove(output_place)
        remove(output_schedule)
        remove(output_last_id)
        print("Data successfully inserted.")
    else:
        print("Data Already Exists")
        return None
    
def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]
