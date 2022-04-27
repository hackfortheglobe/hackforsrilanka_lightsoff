from rest_framework import serializers
from ..models import ScheduleGroup, Place
from django_celery_beat.models import PeriodicTask, ClockedSchedule
from django.db import transaction 
from datetime import datetime, timedelta
from django.utils import timezone

class CreateScheduleSerializer(serializers.ModelSerializer):

    class Meta:
        model = ScheduleGroup
        fields = '__all__'

    @transaction.atomic
    def create(self, validated_data):
        obj = ScheduleGroup(**validated_data)
        time = datetime.now(tz=timezone.utc) + timedelta(minutes=10)
        clock_time = ClockedSchedule.objects.create(clocked_time=time)
        periodict_task = PeriodicTask.objects.create(clocked=clock_time,
                                                    one_off=True,
                                                    task="send_sms_notification",
                                                    name=f'send_bulk_sms{clock_time.id}')
        obj.periodic_task = periodict_task
        obj.save()
        return obj

class PublicScheduleSerializer(serializers.ModelSerializer):
    group_name = serializers.CharField(source='group_name.name')

    class Meta:
        model = ScheduleGroup
        fields = ("starting_period", "ending_period", "group_name")


class CreatePlaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Place
        fields = '__all__'


