# Generated by Django 3.2.7 on 2021-10-03 01:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sitemap', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitemap',
            name='time_fetched',
            field=models.DateTimeField(auto_now_add=True, default=None),
            preserve_default=False,
        ),
    ]