# Generated by Django 3.2.7 on 2021-09-20 00:29

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='PageChangeFrequency',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.CharField(max_length=31, unique=True)),
                ('name', models.CharField(max_length=31, unique=True)),
                ('durationRep', models.DurationField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Sitemap',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url', models.CharField(max_length=511)),
                ('sitemap_type', models.CharField(choices=[('ROBO', 'robots.txt'), ('ATOM', 'RSS 0.3 / 1.0'), ('RSS', 'RSS 2.0'), ('TEXT', 'Plain text'), ('XML', 'XML')], max_length=4)),
                ('is_index', models.BooleanField()),
                ('is_invalid', models.BooleanField()),
                ('invalid_reason', models.CharField(max_length=511, null=True)),
                ('index_sitemap', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='all_sitemaps', to='sitemap.sitemap')),
                ('parent_sitemap', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sub_sitemaps', to='sitemap.sitemap')),
            ],
        ),
        migrations.CreateModel(
            name='Page',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url', models.CharField(max_length=511)),
                ('priority', models.FloatField()),
                ('last_modified', models.DateTimeField(null=True)),
                ('change_frequency', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sitemap.pagechangefrequency')),
                ('index_sitemap', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='all_pages', to='sitemap.sitemap')),
                ('parent_sitemap', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='pages', to='sitemap.sitemap')),
            ],
        ),
    ]
