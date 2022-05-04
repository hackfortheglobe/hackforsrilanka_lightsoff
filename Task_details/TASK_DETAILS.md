# API documentation
https://documenter.getpostman.com/view/11889792/UyrG9syp#6fc48e5a-4da7-4853-99dd-69210c46ff70

# Cron tasks documentation

## send_sms_notification
This method is used to call by the cron job after successfully run the create schedules api.In which filtering the data which is about to run and using schedules group name fetching all the subscribed user from database and devided into batches each batch contain 100 subscriber data and sending message according to batch data.

## send_sms_to_batch
This method call by cron job if the message is not successfully sent to subcriber user's. It will retry to send message to subscriped user's according to provided value(SEND_SMS_MAX_RETRY) in .env file.

## scrapper_data
This method call by cron job in every 10min and in which it will call the scrapper script and stored last scrapped id in database and this method will also call to create schedules and create place apis.


# Table created in database

## GroupName
	This table is store group name which is unique.

## Subscriber:-
This table is store all subscriber details.

## SmsApiAccessToken
This table used to reduce sms login api calling.This table will stored the sms apis access token.

## Transaction
Sms send api key every time gets new unique transcation id so to provide unique transcation id and also check the transcation status used this table.

## ScheduleGroup
It will store the all scheduels along with group name.

## Place
This table is used to store the areas, gcc, feeders and group name here areas are unique for particular gcc.

## Batch
This will contain every details of subscriber, schedule group, transcation and batch status.

## LastProcessedDocument
This will store the last calling scrapper id so that every time scrapper task is calling.
