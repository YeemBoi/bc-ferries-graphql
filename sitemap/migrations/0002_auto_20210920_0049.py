# Generated by Django 3.2.7 on 2021-09-20 00:49

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('sitemap', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sitemap',
            name='index_sitemap',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='all_sitemaps', to='sitemap.sitemap'),
        ),
        migrations.AlterField(
            model_name='sitemap',
            name='parent_sitemap',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sub_sitemaps', to='sitemap.sitemap'),
        ),
    ]
