from django.conf import settings
from core import models as m

from common.scraper_utils import request_soup
from urllib.parse import urlparse
import ujson

from datetime import date

def service(name: str, is_additional: bool) -> m.Service:
    amenity, created = m.Service.objects.get_or_create(name=name, is_additional=is_additional)
    if created:
        print('Created service', amenity)
    return amenity

def run():
    for n in range(settings.SCRAPER_FLEET_PAGE_RANGE):
        soup = request_soup(settings.SCRAPER_FLEET_URL.format(n))
        for bx in soup.select('div[class="ferry-bx"]'):
            ferry_url =  settings.SCRAPER_URL_PREFIX + bx.find('a')['href']
            print('Found ferry url', ferry_url)
            f_page = request_soup(ferry_url)
            f_details = f_page.select_one('.ferrydetails-accordion-sec')
            f_main = f_page.find('div', id='ferryDetails')
            code = list(filter(None, urlparse(ferry_url).path.split('/')))[-1]
            print('Code:', code)
            name = f_main.find('h3').find('strong').get_text(strip=True)
            print('Name:', name)

            onboard_service_c = f_details.select_one('.tabel-ferry-build') # typo is in site
            
            build_stats = dict()
            build_stat_items = f_details.select_one('.ferrydetails-build-statistics'
                ).select('li[class="list-group-item"]')
            for item in build_stat_items:
                build_stat_key = item.select_one('.information-data').get_text(strip=True).upper()
                build_stat_val = item.select_one('.information-value').get_text(strip=True).upper()
                build_stats[build_stat_key] = build_stat_val
            print('Build stats:', build_stats)

            services = []
            for item in onboard_service_c.find('ul').find_all('img'):
                amenityImgSrc = urlparse(ujson.loads(item['data-media'])["1"]).path
                services.append(service(settings.SCRAPER_AMENITY_IMAGE_PATHS.get(amenityImgSrc, amenityImgSrc), False))

            for item in onboard_service_c.select('.ferrydetails-onboard-sec'):
                services.append(service(item.select_one('.col-lg-10').get_text(strip=True), True))
            print('Services:', services)

            m.Ferry.objects.filter(code=code).delete()
            ferry = m.Ferry(
                code = code,
                name = name,
                official_page = ferry_url,
                car_capacity = int(build_stats.get('CAR CAPACITY', 0)),
                human_capacity = int(build_stats.get('PASSENGER & CREW CAPACITY', 0)),
                horsepower = int(build_stats.get('HORSEPOWER', 0)),
                max_displacement = float(build_stats.get('MAXIMUM DISPLACEMENT (T)', 0)),
                max_speed = float(build_stats.get('MAXIMUM SPEED (KNOTS)', 0)),
                total_length = float(build_stats.get('OVERALL LENGTH (M)', 0)),
            )
            built = build_stats.get('BUILT', '').split(',')
            for built_val in built:
                try:
                    ferry.built = date(int(built_val), 1, 1)
                    print('Built:', ferry.built)
                    break
                except ValueError as e:
                    print(e)
            
            ferry.save()
            ferry.services.set(services)
            print('Created ferry', ferry)
            print('\n')

            #   sleep(settings.SCRAPER_PAUSE_SECS)
            #   f_modal = bs(
            #   requests.get(settings.SCRAPER_URL_PREFIX+'/ferry-info', {'code': ferry.code}).json()['ferryInfoModalHtml'],
            #       'html.parser')
