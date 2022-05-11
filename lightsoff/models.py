from click import group
from django.db import models
from django.utils.crypto import get_random_string
from django.core.validators import RegexValidator
from django_celery_beat.models import PeriodicTask
import uuid
from django.contrib.postgres.fields import ArrayField


def generate_random_token():
    return get_random_string(length=32)

class GroupName(models.Model):
    name = models.CharField(max_length=5)

    def __str__(self):
        return '{}'.format(self.name)

class Subscriber(models.Model):
    phone_number_regex = RegexValidator(regex=r'^\d{9}$',
                                        message="Phone number must be entered in the format '23456789'. Up to 9 digits allowed.")
    mobile_number = models.CharField(validators=[phone_number_regex], max_length=9, unique=True)
    name = models.CharField(max_length=50, blank=True, null=True)
    area = models.CharField(max_length=150, blank=True, null=True)
    group_name = models.ForeignKey(GroupName,
                            on_delete=models.CASCADE,
                            null=True,
                            blank=True)
    is_verified = models.BooleanField(default=False)
    is_unsubscribed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '{} - {}'.format(self.group_name, self.mobile_number)


# class Notification(models.Model):
#     SUCCESS = 'SUCCESS'
#     PENDING = 'PENDING'
#     FAILED = 'FAILED'

#     NOTIFICATION_STATUS = (
#         (SUCCESS, "SUCCESS"),
#         (PENDING, "PENDING"),
#         (FAILED, "FAILED"),
#         )

#     user_sub_ref = models.ForeignKey(Subscriber, on_delete=models.CASCADE)
#     notify_status = models.CharField(choices=NOTIFICATION_STATUS, max_length=10)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     def __str__(self):
#         return self.notify_status



class Fetch(models.Model):
    group = models.CharField(max_length=200)
    date = models.DateField()
    hash = models.CharField(max_length=32)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.group} {self.date}"

class SmsApiAccessToken(models.Model):
    access_token = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    expired_at = models.DateTimeField(null=True)


class Transaction(models.Model):
    SUCCESS = 'SUCCESS'
    FAILED = 'FAILED'

    TX_STATUS = (
        (SUCCESS, "SUCCESS"),
        (FAILED, "FAILED"),
        )
    tx_id = models.CharField(max_length=8,
                             blank=True,
                             null=True)
    campaingn_id = models.CharField(max_length=8,
                                    blank=True,
                                    null=True)
    campaingn_cost = models.FloatField(blank=True,
                                       null=True)
    user_id = models.CharField(max_length=8,
                              blank=True,
                              null=True)
    status = models.CharField(choices=TX_STATUS,
                              max_length=10,
                              null=True)
    created_at = models.DateTimeField(auto_now_add=True,
                                      blank=True,
                                      null=True)




class ScheduleGroup(models.Model):
    starting_period = models.DateTimeField()
    ending_period = models.DateTimeField()
    group_name = models.ForeignKey(GroupName,
                                   on_delete=models.CASCADE,
                                   null=True)
    is_run = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Place(models.Model):
    suburb = models.TextField(blank=True, null=True)
    gss = models.TextField()
    area = models.TextField()
    groups = models.ManyToManyField(GroupName)
    feeders = ArrayField(models.CharField(max_length=35))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Batch(models.Model):
    SUCCESS = 'SUCCESS'
    FAILED = 'FAILED'

    BATCH_STATUS = (
        (SUCCESS, "SUCCESS"),
        (FAILED, "FAILED"),
        )
    subscriber = models.ManyToManyField(Subscriber)
    transaction = models.ForeignKey(Transaction,
                                    on_delete=models.CASCADE)
    status = models.CharField(choices=BATCH_STATUS,
                              max_length=10)
    message = models.TextField()
    schedule = models.ForeignKey(ScheduleGroup,
                                 on_delete=models.CASCADE)
    is_batch_run = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True,
                                      null=True)
    updated_at = models.DateTimeField(auto_now=True,
                                      null=True)


class LastProcessedDocument(models.Model):
    last_processed_id = models.CharField(max_length=150)


class SuburbPlace(models.Model):
    suburb = models.TextField()
    gss = models.TextField()
    area = models.TextField()



