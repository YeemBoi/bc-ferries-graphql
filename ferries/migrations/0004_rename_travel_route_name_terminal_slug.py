# Generated by Django 3.2.8 on 2021-10-16 00:14

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ferries', '0003_auto_20211011_1839'),
    ]

    operations = [
        migrations.RenameField(
            model_name='terminal',
            old_name='travel_route_name',
            new_name='slug',
        ),
    ]
