from rest_framework import serializers
from ..models import ScheduleGroup, Place, Subscriber, DistrictPlace
from datetime import datetime, timedelta


class UserSubscriptionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Subscriber
        fields = ("mobile_number", "name" , 'area'
                  ,"group_name" , "is_verified",
                  "is_unsubscribed")


class GetAllSubscribedUserSerializer(serializers.ModelSerializer):
    group_name = serializers.CharField(source='group_name.name')

    class Meta:
        model = Subscriber
        fields = ("mobile_number", "name" , 'area'
                  ,"group_name" , "is_verified",
                  "is_unsubscribed")


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
        fields = ("district", "gss", "area", "groups", "feeders")


class DistrictSerializer(serializers.ModelSerializer):
    groups = serializers.SerializerMethodField()

    class Meta:
        model = Place
        fields = ("district", "gss", "area", "groups", "feeders")

    def get_groups(self, obj):
        return obj.groups.all().values_list("name")