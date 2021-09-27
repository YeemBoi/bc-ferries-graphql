from usp.tree import sitemap_tree_for_homepage

from django.conf import settings
from sitemap.utils import save_sitemap
from sitemap import models as m

# See https://github.com/mediacloud/ultimate-sitemap-parser/issues/1
def run():
    full_sitemap = sitemap_tree_for_homepage(settings.SCRAPER_URL_PREFIX+'/')
    m.Sitemap.objects.all().delete()
    m.Page.objects.all().delete()
    save_sitemap(full_sitemap)
