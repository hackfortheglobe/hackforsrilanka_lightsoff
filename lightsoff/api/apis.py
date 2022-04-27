from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import *
from ..models import *
from rest_framework import status
from django_celery_beat.models import PeriodicTask, ClockedSchedule
from datetime import datetime, timezone
from django.db.models import Q
from django.utils import timezone


class CreateSchedule(APIView):

    def post(self, request):
        error_arr = []
        for index, data in enumerate(request.data["schedules"]):
            group_name = GroupName.objects.filter(name__iexact=data.get("group_name").strip()).first()
            if not group_name:
                group_name = GroupName.objects.create(name=data.get("group_name"))
            request.data["schedules"][index]["group_name"] = group_name.id
            data["starting_period"] = datetime.strptime(data.get("starting_period"), "%d/%m/%Y %H:%M").strftime('%Y-%m-%d %H:%M:%S')
            data["ending_period"] = datetime.strptime(data.get("ending_period"), "%d/%m/%Y %H:%M").strftime('%Y-%m-%d %H:%M:%S')
            serializer = CreateScheduleSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
            else:
                error_arr.append({"group_name": group_name.name,
                                  "description": serializer.errors})
        if len(error_arr) == 0:
            return Response({"message": "success", "errors": error_arr})
        else:
            return Response({"message": "Some group data is not inserted.",
                            "error": error_arr},
                             status=status.HTTP_400_BAD_REQUEST)

class GetAllPublicSchedule(APIView):

    def get(self, request):
        serializer = PublicScheduleSerializer(data=ScheduleGroup.objects.all())
        return Response({"message": "", "data": serializer.data})


class SchedulesByGroup(APIView):

    def get(self, request, group, *args):
        from_date = args.get("from_date", None)
        to_date = args.get("to_date", None)
        if from_date and to_date:
            schedule_group = ScheduleGroup.objects.filter(created_at__date__range=[from_date, to_date],
                                                          group__in=group.upper())
        else:
            schedule_group = ScheduleGroup.objects.filter(updated_at__date__gt=timezone.now().today())
        serializer = Schedule_group(data=ScheduleGroup.objects.all())
        return Response({"message": "", "data": serializer.data})


class SchedulesByPlace(APIView):

    def get(self, request, place, *args):
        from_date = args.get("from_date", None)
        to_date = args.get("to_date", None)
        if from_date and to_date:
            schedule_place = Place.objects.filter(Q(Q(gcc__icontains=place) | Q(area__icontains=place)) \
                                                  & Q(updated_at__date__gt=timezone.now().today()))
        else:
            schedule_place = Place.objects.filter(Q(created_at__date__range=[from_date, to_date])\
                                                  & Q(Q(gcc__icontains=place) | Q(area__icontains=place)))
        serializer = Schedule_group(data=ScheduleGroup.objects.all())
        return Response({"message": "", "data": serializer.data})

class PlaceView(APIView):

    def post(self, request):
        serializer = CreatePlaceSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Successfully inserted."})
        else:
            return Response({"message": "Provided data is invalid."},
                             status=status.HTTP_400_BAD_REQUEST)


class AllGroup(APIView):
    def get(self, request):
        pass
