from rest_framework import serializers
from ..models import ScheduleGroup, Place, Subscriber, SuburbPlace
from datetime import datetime, timedelta


class UserSubscriptionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Subscriber
        fields = ("mobile_number", "name" , 'area'
                  ,"group_name" , "is_verified",
                  "is_unsubscribed")


class UnsubscribedSerializer(serializers.ModelSerializer):

    class Meta:
        model = Subscriber
        fields = ("mobile_number", "is_unsubscribed",)


class CreateScheduleSerializer(serializers.ModelSerializer):

    class Meta:
        model = ScheduleGroup
        fields = ("starting_period", "ending_period",
                  "group_name", "is_run")

class PublicScheduleSerializer(serializers.ModelSerializer):
    group_name = serializers.CharField(source='group_name.name')

    class Meta:
        model = ScheduleGroup
        fields = ("starting_period", "ending_period", "group_name")


class CreatePlaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Place
        fields = ("suburb", "gss", "area", "groups", "feeders")


class SuburbSerializer(serializers.ModelSerializer):
    class Meta:
        model = SuburbPlace
        fields = ("suburb", "gss", "area")

