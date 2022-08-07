import datetime
# import hashlib
import requests
from django.conf import settings
# from django.core.mail import EmailMultiAlternatives
# from django.utils.html import strip_tags
# from lightsoff.models import Fetch
from .models import SmsApiAccessToken, Transaction
from datetime import timedelta
import pyotp
from random import random
from math import floor
from pytz import timezone as pytz_timezones

local_time = pytz_timezones(settings.TIME_ZONE)

# def commit_response_to_db_or_false(response, group, date):
#     """Stores a hash of a request to the database.
#     This is to prevent duplicate requests and notifications
#     for the same day.

#     Args:
#         response (json): The response from the API
#         group (group): The group name
#         date (datetime.date): The date of power cutoffs

#     Returns:
#         bool: Returns True if the response was stored in the database,
#             False otherwise.
#     """
#     json_string = json.dumps(response, sort_keys=True)
#     hash = hashlib.md5(json_string.encode()).hexdigest()
#     if Fetch.objects.filter(group=group, date=date, hash=hash).exists():
#         return False
#     Fetch.objects.create(group=group, date=date, hash=hash)
#     return True


# def query_schedule(group, start_date, end_date):
#     """Queries the API for the schedule for a group
#     between two dates.

#     Args:
#         group (str): The group name
#         start_date (datetime.date): The start date
#         end_date (datetime.date): The end date

#     Returns:
#         dict: A dictionary containing the schedule
#     """
#     response = requests.get(
#         f"{settings.API_BASE_URL}/api/illuminati/powerschedules/{group}",
#         params={
#             "start_date": start_date.isoformat(),
#             "end_date": end_date.isoformat(),
#         },
#     )
#     return response.json()


# def get_schedule_date(group, date):
#     """Gets the schedule for a group on a specific date.

#     Args:
#         group (str): The group name
#         date (datetime.date): The date

#     Returns:
#         dict: A dictionary containing the schedule
#     """
#     query_start_time = datetime.datetime.combine(date, datetime.time.min)
#     query_end_time = datetime.datetime.combine(date, datetime.time.max)
#     return query_schedule(group, query_start_time, query_end_time)


# def get_schedule_bulk(group, start_date, end_date):
#     """Gets the schedule for a group between two dates.

#     Args:
#         group (str): The group name
#         start_date (datetime.date): The start date
#         end_date (datetime.date): The end date

#     Returns:
#         dict: A dictionary containing the schedule
#     """
#     query_start_time = datetime.datetime.combine(start_date, datetime.time.min)
#     query_end_time = datetime.datetime.combine(end_date, datetime.time.max)
#     return query_schedule(group, query_start_time, query_end_time)


# def send_mass_notification(emails, unsubscribe_tokens, group, date, schedule_text):
#     """Sends a mass notification to a list of emails.

#     Args:
#         emails (list): A list of emails
#         unsubscribe_tokens (list): A list of unsubscribe tokens, in the same order as emails
#         group (str): The group name
#         date (datetime.date): The date of power cutoffs
#         from_time (datetime.time): The start time of power cutoffs
#         to_time (datetime.time): The end time of power cutoffs
#     """

#     # Construct the message to send
#     # TODO: Move this out of here, and out domain into a variable.
#     body = f"""
#     <p style="font-size:14px">
#         There will be a scheduled power cutoff for group {group} <b>tomorrow</b>, {date} at these times:
#     </p>
#     <ul style="font-size:14px">
#     """
#     for i in range(len(schedule_text)):
#         body += f"""
#         <li>
#             {schedule_text[i]}
#         </li>
#         """
#     body += """
#     </ul>
#     <p style="font-size:10px;color: gray;">
#         Click <a href="https://lightsoff.herokuapp.com/unsubscribe/{token}">here</a> to unsubscribe.
#     </p>
#     """

#     plain_message = strip_tags(body)

#     msg = EmailMultiAlternatives(
#         f"Power Cutoff Schedule for Tomorrow, {date}", plain_message, None, emails
#     )
#     msg.attach_alternative(body, "text/html")
#     msg.send()

#     msg.merge_data = {
#         emails[i]: {"unsubscribe_token": unsubscribe_tokens[i]}
#         for i in range(len(emails))
#     }

#     msg.send()
#     print("Sent mass notification")


# # TODO: Implement this feature
# def determine_group_by_geolocation():
#     pass

# import timezone



def login_sms_api():
    now_time = datetime.datetime.now(tz=local_time)
    stored_token = SmsApiAccessToken.objects.filter(expired_at__gt=now_time).order_by("-id").first()
    if stored_token:
        old_token=stored_token.access_token
        print(f"Dialog login - Reusing previous token: {stored_token.id}# {old_token[-10:]}")
        return old_token
    else:
        url = "https://e-sms.dialog.lk/api/v1/login"
        user_credentials = {"username": settings.SMS_API_USERNAME,
                            "password": settings.SMS_API_PASSWORD}
        res_data = requests.post(url, data=user_credentials)
        expired_token_time = datetime.datetime.now(tz=local_time) + timedelta(hours=11, minutes=50)
        if res_data.status_code == 200:
            if res_data.json().get("errCode") == '':
                data = res_data.json()
                new_token = data.get("token")
                print(f"Dialog login: obtained new token {new_token[-10:]}")
                SmsApiAccessToken.objects.create(access_token=new_token,
                                                 expired_at=expired_token_time)
                return new_token
        print(f"Dialog login: unable to obtain token")
        raise Exception("Credential's are invalide for sms api.")



def get_totp(key=None):
    '''
    Returns a pyotp.TOTP instance to generate and verify OTP
    '''
    # generate random secret key
    if not key:
        key = pyotp.random_base32()
    totp = pyotp.TOTP(key, digits=settings.OTP_NUM_DIGITS, interval=settings.OTP_EXPIRE_SECONDS)
    return totp, key

import json
from requests.structures import CaseInsensitiveDict

def send_sms(numbers, message, tx_id):
    headers = CaseInsensitiveDict()
    access_token = login_sms_api()
    url = "https://e-sms.dialog.lk/api/v1/sms"
    headers["Authorization"] = f"Bearer {access_token}"
    headers["Content-Type"] = "application/json"
    data = {
            "sourceAddress": settings.SMS_MASK_NAME,
            "message": message,
            "transaction_id": tx_id,
            "msisdn": numbers
            }
    resp = requests.post(url, headers=headers, data=json.dumps(data))
    print(data)
    print(resp.json())
    return resp

def convert_into_datetime(date_time_data):
    naive = datetime.datetime.strptime(date_time_data,
                                       '%Y-%m-%d %H:%M')
    local_dt = local_time.localize(naive, is_dst=None)
    return local_dt

def generate_uniqe_id():
    digits = "0123456789"
    tx_id = ""
    while True:
        for i in range(8):
            tx_id += digits[floor(random() * 10)]
        tx_id = int(tx_id)
        if not Transaction.objects.filter(tx_id=tx_id).first():
            return tx_id


