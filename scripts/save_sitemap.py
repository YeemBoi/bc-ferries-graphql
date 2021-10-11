from usp.tree import sitemap_tree_for_homepage

from common.scraper_utils import SCRAPER_SETTINGS
from sitemap.utils import save_sitemap
from sitemap import models as m

# See https://github.com/mediacloud/ultimate-sitemap-parser/issues/1
def run():
    full_sitemap = sitemap_tree_for_homepage(SCRAPER_SETTINGS.URL_PREFIX+'/')
    m.Sitemap.objects.all().delete()
    m.Page.objects.all().delete()
    save_sitemap(full_sitemap)
