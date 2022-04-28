from django.contrib import admin
from lightsoff.models import *

admin.site.register(Subscriber)
admin.site.register(Fetch)

admin.site.register(ScheduleGroup)
admin.site.register(GroupName)
admin.site.register(Transaction)
admin.site.register(Batch)
admin.site.register(SmsApiAccessToken)
admin.site.register(Place)