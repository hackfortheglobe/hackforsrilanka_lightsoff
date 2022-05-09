from __future__ import absolute_import
import os
from celery import Celery
from celery.schedules import crontab
from django.conf import settings

# set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "conf.settings")
app = Celery("lightsoff")

app.config_from_object("django.conf:settings",namespace='CELERY')
app.autodiscover_tasks()
# app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


@app.task(bind=True)
def debug_task(self):
    print("Request: {0!r}".format(self.request))


app.conf.beat_schedule = {
    #
    #     'add-every-5-seconds':{
    #         'task':'datafeed.tasks.add_newmyfunction',
    #         'schedule': crontab(),
    #         # 'schedule': 5.0,
    #         'options':{
    #             'link':signature('datafeed.tasks.new_func',args=(),kwargs=())
    #         }
    #     },

    'every-day-eve': {
        'task': 'lightsoff.tasks.scrapper_data',
        'schedule': crontab(hour=17,minute=16),
        # 'schedule': crontab(hour=18,minute=46,day_of_week='mon-fri'),
        # 'schedule': crontab(hour='9-15/1', minute=15, day_of_week='mon-fri', ),
        # 'options':{
        #     'link':signature('datafeed.neeraj_t.live_forex',args=(),kwargs=())
        # }
    },
}

