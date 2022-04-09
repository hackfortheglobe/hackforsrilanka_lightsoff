from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from django.core.mail import send_mail


class SendTestEmail(APIView):
    permission_classes = []

    def get(self, request):
        send_mail(
            "It works!",
            "This will get sent through Mailgun",
            "Anymail Sender <from@example.com>",
            ["itsrashidalabri@gmail.com"],
        )
        return Response({"message": "Hello, world!"})
