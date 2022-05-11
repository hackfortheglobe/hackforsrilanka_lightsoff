from django_celery_beat.models import PeriodicTask, PeriodicTasks

def run():
	obj = PeriodicTask.objects.filter(name="scrapper_data").first()
	if obj:
		obj.last_run_at = None
		obj.save()
		print("----------Periodict Task Script called------------")