from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import *
from ..models import *
from rest_framework import status
from django_celery_beat.models import PeriodicTask, ClockedSchedule
from ..utils import *
from rest_framework_api_key.permissions import HasAPIKey
from datetime import datetime, timedelta


class SendOtp:

    def send_phone_otp(self, phone_number, otp):
        tx_id = generate_uniqe_id()
        message = f"Please enter this {otp} to verify your mobile number."
        resp = send_sms([phone_number], message, tx_id)
        if resp.status_code == 200:
            res_data = resp.json()
            tx_data = Transaction.objects.create(campaingn_id=res_data["data"].get("campaignId", None),
                                                 campaingn_cost=res_data["data"].get("campaignCost", None),
                                                 user_id=res_data["data"].get("userId", None),
                                                 status="SUCCESS",
                                                 tx_id=tx_id)
            return True
        else:
            res_data = resp.json()
            tx_data = Transaction.objects.create(status="FAILED",
                                                 tx_id=tx_id)
            return False


class UserSubscription(APIView, SendOtp):

    def post(self, request):
        new_user = Subscriber.objects.filter(mobile_number=request.data["mobile_number"].strip(),
                                             is_unsubscribed=False).first()
        group_name = request.data["group_name"]
        if new_user:
            return Response({"message":"", "errors": f"You are already subscribed with group '{new_user.group_name}', " \
                                                      f"do you want to subscribe with a different group '{group_name}' ?"
                             },status=status.HTTP_409_CONFLICT)
        user = Subscriber.objects.filter(mobile_number=request.data["mobile_number"].strip(),
                                         is_unsubscribed=True).first()
        group_name = GroupName.objects.filter(name=request.data["group_name"]).first()
        totp, secret_key = get_totp()
        if group_name:
            request.data["group_name"] = group_name.id
            serializer = UserSubscriptionSerializer(data=request.data)
            if serializer.is_valid():
                phone_number = request.data.get("mobile_number")
                numbers = {"mobile": phone_number}
                self.send_phone_otp(numbers, totp.now())
                return Response({"message": "Please verify your mobile to providing otp.",
                                "secret_key": secret_key,
                                "mobile_number": phone_number})
            else:
                return Response({"message": "", "errors": serializer.errors},
                                status=status.HTTP_400_BAD_REQUEST)
        return Response(
                    {'message': 'You have to provide the group name.'},
                    status=status.HTTP_400_BAD_REQUEST
                )


class ChangeSubscriberGroup(APIView, SendOtp):

    def post(self, request):
        new_user = Subscriber.objects.filter(mobile_number=request.data["mobile_number"].strip(),
                                             is_unsubscribed=False).first()
        group_name = request.data["group_name"]
        if not new_user:
            return Response({"message":"", "errors": "User does not exist."})

        group_name = GroupName.objects.filter(name=request.data["group_name"]).first()
        if group_name:
            request.data["group_name"] = group_name.id
        phone_number = request.data.get("mobile_number")
        numbers = {"mobile": phone_number}
        totp, secret_key = get_totp()
        self.send_phone_otp(numbers, totp.now())
        if new_user:
            serializer = UserSubscriptionSerializer(data=request.data,
                                                    instance=new_user,
                                                    partial=True)
            if serializer.is_valid():
                return Response({"message": "Please verify your mobile to providing otp.",
                                "secret_key": secret_key,
                                "mobile_number": phone_number})
            else:
                return Response({"message": "", "errors": serializer.errors},
                                status=status.HTTP_400_BAD_REQUEST)
        return Response(
                    {'message': 'You have to provide the group name.'},
                    status=status.HTTP_400_BAD_REQUEST
                )


class VerifyOtp(APIView):

    def post(self, request):
        otp = request.data.get('otp')
        totp, secret_key = get_totp(key=request.data.get('secret_key'))
        group_name = GroupName.objects.filter(name=request.data["group_name"]).first()
        if group_name:
            request.data["group_name"] = group_name.id
            new_user = Subscriber.objects.filter(mobile_number=request.data["mobile_number"].strip(),
                                                     is_unsubscribed=False).first()
            if totp.verify(otp):
                if new_user:
                    new_user.delete()
            else:
                return Response(
                {'message': 'OTP is either expired or invalid, please try again'},
                status=status.HTTP_400_BAD_REQUEST)
            serializer = UserSubscriptionSerializer(data=request.data)
            if serializer.is_valid():
                user = serializer.save()
                user.is_verified = True
                user.save()
                return Response(
                    {'message': 'OTP is verified successfully and your subscription has been done.'}
                )
            return Response(
                {'message': 'OTP is either expired or invalid, please try again'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(
                    {'message': 'You have to provide group name.'},
                    status=status.HTTP_400_BAD_REQUEST
                )


class Unsubscribed(APIView):

    def post(self, request):
        user = Subscriber.objects.filter(mobile_number=request.data["mobile_number"].strip()).first()
        if user:
            user.delete()
            return Response({"message": "Unsubscribed successfully."})
        else:
            return Response({"message": "", "errors": "Account not found with this number."},
                            status=status.HTTP_404_NOT_FOUND)

class CreateSchedule(APIView):
    permission_classes = [HasAPIKey]

    def post(self, request):
        error_arr = []
        for index, data in enumerate(request.data["schedules"]):
            try:
                group_name = GroupName.objects.filter(name__iexact=data.get("group").strip()).first()
                if not group_name:
                    group_name = GroupName.objects.create(name=data.get("group"))
                request.data["schedules"][index]["group_name"] = group_name.id
                data["starting_period"] = data.get("starting_period")
                data["ending_period"] = data.get("ending_period")
                serializer = CreateScheduleSerializer(data=data)
                if serializer.is_valid():
                    serializer.save()
                else:
                    error_arr.append({"group_name": group_name.name,
                                      "description": serializer.errors})
            except Exception as e:
                print("Invalid data", str(e))
        if len(request.data["schedules"]) != 0:
            time = datetime.now(tz=local_time) + timedelta(minutes=1)
            clock_time = ClockedSchedule.objects.create(clocked_time=time)
            periodict_task = PeriodicTask.objects.create(clocked=clock_time,
                                                        one_off=True,
                                                        task="lightsoff.tasks.send_sms_notification",
                                                        name=f'send_bulk_sms{clock_time.id}')
        if len(error_arr) == 0:
            return Response({"message": "success", "errors": error_arr})
        else:
            return Response({"message": "Some group data is not inserted.",
                            "error": error_arr},
                             status=status.HTTP_400_BAD_REQUEST)

class GetAllPublicSchedule(APIView):

    def get(self, request):
        serializer = PublicScheduleSerializer(ScheduleGroup.objects.all().order_by("-id"),
                                              many=True)
        return Response({"message": "", "data": serializer.data})


class AllGroupName(APIView):
    def get(self, request):
        data = GroupName.objects.all().values_list("name", flat=True)
        return Response({"message": "", "data": data})

class AllGCCName(APIView):
    def get(self, request):
        data = Place.objects.all().values_list("gss", flat=True).order_by("gss").distinct()
        return Response({"message": "", "data": data})

class AllAreaName(APIView):
    def get(self, request):
        gss = request.query_params.get('gss')
        if gss:
            data = Place.objects.filter(gss=gss).values_list("area", flat=True).order_by("area")
            return Response({"message": "", "data": data})
        else:
            return Response({"message": "",
                             "errors": "gss parameter is required."},
                            status=status.HTTP_400_BAD_REQUEST)

class SchedulesByGroup(APIView):

    def get(self, request, group):
        from_date = request.query_params.get("from_date", None)
        to_date = request.query_params.get("to_date", None)
        if from_date and to_date:
            schedule_group = ScheduleGroup.objects.filter(starting_period__date__gte=from_date,
                                                          ending_period__date__lte=to_date,
                                                          group_name__name=group.upper())
        else:
            schedule_group = ScheduleGroup.objects.filter(created_at__date__gte=datetime.now(tz=local_time).today(),
                                                          group_name__name=group.upper())
        serializer = PublicScheduleSerializer(schedule_group,
                                              many=True)
        return Response({"message": "", "data": serializer.data})


class SearchSchedulesByPlace(APIView):

    def get(self, request):
        area = request.query_params.get("area", None)
        district = request.query_params.get("district", None)
        if district and area and area != "" and district != "":
            from_date = request.query_params.get("from_date", None)
            to_date = request.query_params.get("to_date", None)
            if from_date and to_date:
                schedule_place = Place.objects.filter(gss=district, area=area)
            else:
                schedule_place = Place.objects.filter(gss=district, area=area)
            if len(schedule_place) != 0:
                data = []
                for schedule_data in schedule_place:
                    if from_date and to_date:
                        schedule_group = ScheduleGroup.objects.filter(starting_period__date__gte=from_date,
                                                                      ending_period__date__lte=to_date,
                                                                      group_name__in=schedule_data.groups.all())
                    else:
                        schedule_group = ScheduleGroup.objects.filter(starting_period__date=datetime.now(tz=local_time).today(),
                                                                      group_name__in=schedule_data.groups.all())
                serializer = PublicScheduleSerializer(schedule_group,
                                                      many=True)
                return Response({"message": "", "data": serializer.data})
            else:
                return Response({"message": "", "data": []})
        else:
            return Response({"message": "",
                             "errors": "area and district parameter is required."},
                            status=status.HTTP_400_BAD_REQUEST)

class PlaceView(APIView):
    permission_classes = [HasAPIKey]

    def post(self, request):
        createCount=0
        updateCount=0
        print ("GSS received:",len(request.data))
        for gss_data in request.data:
            try:
                print ("#",request.data.index(gss_data), ": Areas for ", gss_data, " are: ", request.data[gss_data])
                for area_data in request.data[gss_data]:
                    suburb_data = SuburbPlace.objects.filter(gss__iexact=gss_data,
                                                             area__iexact=area_data).first()
                    suburb = ""
                    if suburb_data:
                        suburb = suburb_data.suburb
                    place_obj = Place.objects.filter(gss__iexact=gss_data,
                                                     area__iexact=area_data
                                                     ).first()
                    if not place_obj:
                        place_obj = Place.objects.create(gss=gss_data,
                                                         suburb=suburb,
                                                         area=area_data,
                                                         feeders=request.data[gss_data][area_data]["feeders"])
                        createCount = createCount+1
                    else:
                        place_obj.area = area_data
                        place_obj.suburb = suburb
                        place_obj.feeders = request.data[gss_data][area_data]["feeders"]
                        place_obj.save()
                        updateCount = updateCount+1
                    group_collection = []
                    for group_name in request.data[gss_data][area_data]["groups"]:
                        group_obj = GroupName.objects.filter(name=group_name).first()
                        if not group_obj:
                            group_obj = GroupName.objects.create(name=group_name)
                        group_collection.append(group_obj.id)
                    place_obj.groups.set(group_collection)
            except Exception as e:
                print("Invalid data", str(e))

            print( "Created places: ", createCount)
            print( "Updated places: ", updateCount)
        return Response({"message": "Successfully inserted."})


class GetAllSubscribedUser(APIView):
    def get(self, request):
        user_data = Subscriber.objects.all().order_by("-id")
        serializer = UserSubscriptionSerializer(user_data, many=True)
        return Response({"message": "", "data": serializer.data})


class SearchBySuburb(APIView):
    def get(self, request):
        suburb = request.query_params.get("suburb", None)
        if suburb:
            suburb_data = Place.objects.filter(suburb__iexact=suburb).order_by("gss", "area")
            serializer = CreatePlaceSerializer(suburb_data, many=True)
            return Response({"message":"", "data": serializer.data})
        else:
            return Response({"message": "",
                             "errors": "suburb parameter is required."},
                            status=status.HTTP_400_BAD_REQUEST)


class GetAllSuburb(APIView):
    def get(self, request):
        all_suburb = SuburbPlace.objects.all().order_by("suburb").values_list("suburb", flat=True).distinct()
        return Response({"message": "", "data": all_suburb})