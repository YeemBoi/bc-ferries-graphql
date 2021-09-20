# Generated by Django 3.2.7 on 2021-09-20 02:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sitemap', '0004_alter_page_parent_sitemap'),
    ]

    operations = [
        migrations.RenameField(
            model_name='pagechangefrequency',
            old_name='durationRep',
            new_name='duration_rep',
        ),
        migrations.AlterField(
            model_name='page',
            name='url',
            field=models.URLField(),
        ),
        migrations.AlterField(
            model_name='sitemap',
            name='url',
            field=models.URLField(),
        ),
    ]
