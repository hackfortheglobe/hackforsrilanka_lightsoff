import datetime
from conf.celery import app
from django.core.mail import send_mail
from django.utils import timezone

import dateutil.parser

from lightsoff.models import GROUP_CHOICES, Subscriber
from lightsoff.utils import (
    commit_response_to_db_or_false,
    get_schedule_date,
    send_mass_notification,
)


@app.task()
def send_confirmation_email(email):
    send_mail(
        "LightsOff Subscription Confirmation",
        "You have been subscribed to the Lightsoff newsletter.",
        from_email=None,
        recipient_list=[email],
    )


@app.task()
def send_update_emails():
    for group, _ in GROUP_CHOICES:
        data = Subscriber.objects.filter(group=group).values_list(
            "email", "unsubscribe_token"
        )
        emails = [email for email, _ in data]
        unsubscribe_tokens = [token for _, token in data]

        # Skip if there are no subscribers
        if len(emails) == 0:
            print(f"No subscribers for {group}")
            continue

        tomorrow_date = timezone.localdate() + datetime.timedelta(days=1)
        schedule = get_schedule_date(group, tomorrow_date)

        # Skip if we have already acted upon this schedule update
        if not commit_response_to_db_or_false(schedule, group, tomorrow_date):
            print(f"Already acted upon schedule for {group}")
            continue

        # Skip if there are no power cuts
        if len(schedule) == 0:
            print(f"No power cuts for group {group}")
            continue

        # Create list of human readable strings of the time windows of the cutoffs
        schedule_text = []
        for row in schedule:
            raw_start_time = dateutil.parser.isoparse(row["starting_period"])
            raw_end_time = dateutil.parser.isoparse(row["ending_period"])

            # Convert to local time (Asia / Colombos)
            start_time = timezone.make_aware(
                timezone.make_naive(raw_start_time), timezone.get_current_timezone()
            )
            end_time = timezone.make_aware(
                timezone.make_naive(raw_end_time), timezone.get_current_timezone()
            )
            string = (
                f"{start_time.strftime('%I:%M %p')} - {end_time.strftime('%I:%M %p')}"
            )
            schedule_text.append(string)

        tomorrow_date_readable = tomorrow_date.strftime("%d-%m-%Y")
        send_mass_notification(
            emails, unsubscribe_tokens, group, tomorrow_date_readable, schedule_text
        )
        print("Finished task")
