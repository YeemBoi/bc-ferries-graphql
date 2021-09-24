from usp.tree import sitemap_tree_for_homepage

from django.conf import settings
from sitemap.utils import SaveSitemap
from sitemap import models as m

# See https://github.com/mediacloud/ultimate-sitemap-parser/issues/1
def run():
    fullSitemap = sitemap_tree_for_homepage(settings.SCRAPER_URL_PREFIX+'/')
    m.Sitemap.objects.all().delete()
    m.Page.objects.all().delete()
    SaveSitemap(fullSitemap)
