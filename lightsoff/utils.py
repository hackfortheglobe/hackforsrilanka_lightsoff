import datetime
from tokenize import group

import requests
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags
from pyparsing import html_comment

import hashlib
import json

from lightsoff.models import Fetch


def commit_response_to_db_or_false(response, group, date):
    """Stores a hash of a request to the database.
    This is to prevent duplicate requests and notifications
    for the same day.

    Args:
        response (json): The response from the API
        group (group): The group name
        date (datetime.date): The date of power cutoffs

    Returns:
        bool: Returns True if the response was stored in the database,
            False otherwise.
    """
    json_string = json.dumps(response, sort_keys=True)
    hash = hashlib.md5(json_string.encode()).hexdigest()
    if Fetch.objects.filter(group=group, date=date, hash=hash).exists():
        return False
    Fetch.objects.create(group=group, date=date, hash=hash)
    return True


def query_schedule(group, start_date, end_date):
    """Queries the API for the schedule for a group
    between two dates.

    Args:
        group (str): The group name
        start_date (datetime.date): The start date
        end_date (datetime.date): The end date

    Returns:
        dict: A dictionary containing the schedule
    """
    response = requests.get(
        f"https://hackforsrilanka-api.herokuapp.com/api/illuminati/powerschedules/{group}",
        params={
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        },
    )
    return response.json()


def get_schedule_date(group, date):
    """Gets the schedule for a group on a specific date.

    Args:
        group (str): The group name
        date (datetime.date): The date

    Returns:
        dict: A dictionary containing the schedule
    """
    query_start_time = datetime.datetime.combine(date, datetime.time.min)
    query_end_time = datetime.datetime.combine(date, datetime.time.max)
    return query_schedule(group, query_start_time, query_end_time)


def get_schedule_bulk(group, start_date, end_date):
    """Gets the schedule for a group between two dates.

    Args:
        group (str): The group name
        start_date (datetime.date): The start date
        end_date (datetime.date): The end date

    Returns:
        dict: A dictionary containing the schedule
    """
    query_start_time = datetime.datetime.combine(start_date, datetime.time.min)
    query_end_time = datetime.datetime.combine(end_date, datetime.time.max)
    return query_schedule(group, query_start_time, query_end_time)


def send_mass_notification(emails, unsubscribe_tokens, group, date, schedule_text):
    """Sends a mass notification to a list of emails.

    Args:
        emails (list): A list of emails
        unsubscribe_tokens (list): A list of unsubscribe tokens, in the same order as emails
        group (str): The group name
        date (datetime.date): The date of power cutoffs
        from_time (datetime.time): The start time of power cutoffs
        to_time (datetime.time): The end time of power cutoffs
    """

    # Construct the message to send
    # TODO: Move this out of here, and out domain into a variable.
    body = f"""
    <p style="font-size:14px">
        There will be a scheduled power cutoff for group {group} <b>tomorrow</b>, {date} at these times:
    </p>
    <ul style="font-size:14px">
    """
    for i in range(len(schedule_text)):
        body += f"""
        <li>
            {schedule_text[i]}
        </li>
        """
    body += """
    </ul>
    <p style="font-size:10px;color: gray;">
        Click <a href="https://lightsoff.herokuapp.com/unsubscribe/{token}">here</a> to unsubscribe.
    </p>
    """

    plain_message = strip_tags(body)

    msg = EmailMultiAlternatives(
        f"Power Cutoff Schedule for Tomorrow, {date}", plain_message, None, emails
    )
    msg.attach_alternative(body, "text/html")
    msg.send()

    msg.merge_data = {
        emails[i]: {"unsubscribe_token": unsubscribe_tokens[i]}
        for i in range(len(emails))
    }

    msg.send()
    print("Sent mass notification")


# TODO: Implement this feature
def determine_group_by_geolocation():
    pass
