# Generated by Django 3.2.13 on 2022-04-28 06:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lightsoff', '0018_auto_20220428_1021'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transaction',
            name='campaingn_cost',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='campaingn_id',
            field=models.CharField(blank=True, max_length=8, null=True),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='user_id',
            field=models.CharField(blank=True, max_length=8, null=True),
        ),
    ]
