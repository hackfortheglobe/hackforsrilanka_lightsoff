from rest_framework import serializers
from ..models import ScheduleGroup, Place, Subscriber, SuburbPlace
from django_celery_beat.models import PeriodicTask, ClockedSchedule
from django.db import transaction 
from datetime import datetime, timedelta
from django.utils import timezone


class UserSubscriptionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Subscriber
        fields = '__all__'


class UnsubscribedSerializer(serializers.ModelSerializer):

    class Meta:
        model = Subscriber
        fields = ("mobile_number", "is_unsubscribed",)


class CreateScheduleSerializer(serializers.ModelSerializer):

    class Meta:
        model = ScheduleGroup
        fields = '__all__'

class PublicScheduleSerializer(serializers.ModelSerializer):
    group_name = serializers.CharField(source='group_name.name')

    class Meta:
        model = ScheduleGroup
        fields = ("starting_period", "ending_period", "group_name")


class CreatePlaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Place
        fields = '__all__'


class SuburbSerializer(serializers.ModelSerializer):
    class Meta:
        model = SuburbPlace
        fields = '__all__'

