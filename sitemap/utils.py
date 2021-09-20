from . import models as m
from usp.objects import page, sitemap # type: ignore
from typing import Optional

def SaveSitemap(sm, indexSitemap: Optional[m.Sitemap] = None, parentSitemap: Optional[m.Sitemap] = None):
    smt = type(sm)
    sitemapM = m.Sitemap(
        url = sm.url,
        parent_sitemap = parentSitemap,
        is_index = issubclass(smt, sitemap.AbstractIndexSitemap),
        is_invalid = issubclass(smt, sitemap.InvalidSitemap),
    )

    if sitemapM.is_invalid:
        sitemapM.invalid_reason = sm.reason

    smtStr = str
    if issubclass(smt, sitemap.IndexRobotsTxtSitemap):
        smtStr = 'ROBO'
    elif issubclass(smt, sitemap.IndexXMLSitemap) or issubclass(smt, sitemap.PagesXMLSitemap):
        smtStr = 'XML'
    elif issubclass(smt, sitemap.PagesAtomSitemap):
        smtStr = 'ATOM'
    elif issubclass(smt, sitemap.PagesRSSSitemap):
        smtStr = 'RSS'
    elif issubclass(smt, sitemap.PagesTextSitemap):
        smtStr = 'TEXT'
    sitemapM.sitemap_type = smtStr

    sitemapM.save()
    sitemapM.index_sitemap = indexSitemap or sitemapM
    sitemapM.parent_sitemap = parentSitemap or sitemapM
    sitemapM.save()
    
    if hasattr(sm, 'sub_sitemaps'):
        for newSitemap in sm.sub_sitemaps:
            SaveSitemap(newSitemap, sitemapM.index_sitemap, sitemapM)
    
    if hasattr(sm, 'pages'):
        pages = []
        for page in sm.pages:
            pageM = m.Page(
                parent_sitemap = sitemapM,
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
