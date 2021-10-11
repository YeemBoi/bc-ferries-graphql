from . import models as m
from usp.objects import page, sitemap
from typing import Optional

SITEMAP_CLASS_TYPES = {
    sitemap.IndexRobotsTxtSitemap: 'ROBO',
    sitemap.IndexXMLSitemap: 'XML',
    sitemap.PagesXMLSitemap: 'XML',
    sitemap.PagesAtomSitemap: 'ATOM',
    sitemap.PagesRSSSitemap: 'RSS',
    sitemap.PagesTextSitemap: 'TEXT',
}

def save_sitemap(sm, indexSitemap: Optional[m.Sitemap] = None, parentSitemap: Optional[m.Sitemap] = None):
    smt = type(sm)
    sitemapM = m.Sitemap(
        url = sm.url,
        parent_sitemap = parentSitemap,
        is_index = issubclass(smt, sitemap.AbstractIndexSitemap),
        is_invalid = issubclass(smt, sitemap.InvalidSitemap),
    )
    if sitemapM.is_invalid:
        sitemapM.invalid_reason = sm.reason

    for sm_class, type_name in SITEMAP_CLASS_TYPES.items():
        if issubclass(smt, sm_class):
            sitemapM.sitemap_type = type_name
            break

    sitemapM.save()
    sitemapM.index_sitemap = indexSitemap or sitemapM
    sitemapM.sitemap = parentSitemap or sitemapM
    sitemapM.save()
    
    if hasattr(sm, 'sub_sitemaps'):
        for newSitemap in sm.sub_sitemaps:
            save_sitemap(newSitemap, sitemapM.index_sitemap, sitemapM)
    
    if hasattr(sm, 'pages'):
        pages = []
        for page in sm.pages:
            pageM = m.Page(
                sitemap = sitemapM,
                url = page.url,
                priority = page.priority,
                last_modified = page.last_modified,
            )
            pageM.change_frequency, _ = m.PageChangeFrequency.objects.get_or_create(
                name = page.change_frequency.name,
                value = page.change_frequency.value,
            )
            pages.append(pageM)
        m.Page.objects.bulk_create(pages)
