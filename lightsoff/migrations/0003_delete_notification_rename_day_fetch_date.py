# Generated by Django 4.0.3 on 2022-04-09 22:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lightsoff', '0002_fetch_notification'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Notification',
        ),
        migrations.RenameField(
            model_name='fetch',
            old_name='day',
            new_name='date',
        ),
    ]
