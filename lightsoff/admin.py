from django.contrib import admin
from lightsoff.models import *


admin.site.register(Fetch)


admin.site.register(GroupName)

admin.site.register(SmsApiAccessToken)

admin.site.register(LastProcessedDocument)

class AdminSubscriber(admin.ModelAdmin):
	search_fields = ["mobile_number","group_name__name"]
admin.site.register(Subscriber, AdminSubscriber)

class AdminTransaction(admin.ModelAdmin):
	list_display = ("id","tx_id","status" ,"created_at")
	readonly_fields = ('created_at', )

admin.site.register(Transaction, AdminTransaction)


class AdminScheduleGroup(admin.ModelAdmin):
	list_display = ("id", "group_name", "is_run")
	readonly_fields = ('created_at', )
	search_fields = ["group_name__name"]

admin.site.register(ScheduleGroup, AdminScheduleGroup)


class AdminPlace(admin.ModelAdmin):
	list_display = ("id", "gss", "area")
	readonly_fields = ('updated_at', 'created_at', )

admin.site.register(Place, AdminPlace)

class AdminBatch(admin.ModelAdmin):
	list_display = ("id", "is_batch_run", "status", "transaction")
	readonly_fields = ('updated_at', 'created_at', )

admin.site.register(Batch, AdminBatch)

class AdminSuburbPlace(admin.ModelAdmin):
	list_display = ("id", "suburb", "gss", "area")

admin.site.register(SuburbPlace, AdminSuburbPlace)

