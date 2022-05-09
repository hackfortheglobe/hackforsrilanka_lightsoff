from __future__ import absolute_import
import os
from celery import Celery
from django.conf import settings

# set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "conf.settings")
app = Celery("lightsoff")

app.config_from_object("django.conf:settings")
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

app.conf.update(worker_max_memory_per_child=16000,
                worker_max_tasks_per_child=1)

@app.task(bind=True)
def debug_task(self):
    print("Request: {0!r}".format(self.request))
