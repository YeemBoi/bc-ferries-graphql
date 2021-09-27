from django.conf import settings
from core import models as m

from bs4 import BeautifulSoup as bs
import html5lib
import ujson

from datetime import date

import requests
from urllib.parse import urlparse
from time import sleep

def service(name: str, is_additional: bool) -> m.Service:
    amenity, created = m.Service.objects.get_or_create(name=name, is_additional=is_additional)
    if created:
        print('Created service', amenity)
    return amenity

def run():
    for n in range(settings.SCRAPER_FLEET_PAGE_RANGE):
        sleep(settings.SCRAPER_PAUSE_SECS)
        req = requests.get(settings.SCRAPER_FLEET_URL.format(n))
        req.encoding = req.apparent_encoding
        soup = bs(req.text ,'html5lib')
        for bx in soup.select('div[class="ferry-bx"]'):
            href = bx.find('a')['href']
            print('Found ferry url', href)
            sleep(settings.SCRAPER_PAUSE_SECS)
            f_req = requests.get(settings.SCRAPER_URL_PREFIX+href)
            f_req.encoding = f_req.apparent_encoding
            f_page = bs(f_req.text ,'html5lib')
            f_details = f_page.select_one('.ferrydetails-accordion-sec')
            f_main = f_page.find('div', id='ferryDetails')
            code = list(filter(None, urlparse(href).path.split('/')))[-1]
            print('Code:', code)
            name = f_main.find('h3').find('strong').get_text(strip=True)
            print('Name:', name)

            onboard_service_c = f_details.select_one('.tabel-ferry-build') # typo is in site
            
            build_stats = dict()
            build_statItems = f_details.select_one('.ferrydetails-build-statistics'
                ).select('li[class="list-group-item"]')
            for item in build_statItems:
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

            m.Ship.objects.filter(code=code).delete()

            ship = m.Ship(
                code = code,
                name = name,
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
                    ship.built = date(int(built_val), 1, 1)
                    print('Built:', ship.built)
                    break
                except ValueError as e:
                    print(e)
            
            ship.save()

            for new_service in services:
                ship.services.add(new_service)

            print('Created ship', ship)
            print('\n')

            #   sleep(settings.SCRAPER_PAUSE_SECS)
            #   f_modal = bs(
            #   requests.get(settings.SCRAPER_URL_PREFIX+'/ship-info', {'code': ship.code}).json()['shipInfoModalHtml'],
            #       'html.parser')
