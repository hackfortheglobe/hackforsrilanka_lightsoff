import celery

app = celery.Celery("lightsoff")


@app.task()
def scheduledTask():
    print("Hi")
