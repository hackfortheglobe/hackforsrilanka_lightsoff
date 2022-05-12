# Generated by Django 3.2.13 on 2022-05-12 10:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lightsoff', '0031_place_suburb'),
    ]

    operations = [
        migrations.CreateModel(
            name='districtPlace',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('district', models.TextField()),
                ('gss', models.TextField()),
                ('area', models.TextField()),
            ],
        ),
        migrations.DeleteModel(
            name='SuburbPlace',
        ),
        migrations.RenameField(
            model_name='place',
            old_name='suburb',
            new_name='district',
        ),
    ]
