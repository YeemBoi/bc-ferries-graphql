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
            fReq = requests.get(settings.SCRAPER_URL_PREFIX+href)
            fReq.encoding = fReq.apparent_encoding
            fPage = bs(fReq.text ,'html5lib')
            fDetails = fPage.select_one('.ferrydetails-accordion-sec')
            fMain = fPage.find('div', id='ferryDetails')
            code = list(filter(None, urlparse(href).path.split('/')))[-1]
            print('Code:', code)
            name = fMain.find('h3').find('strong').getText(strip=True)
            print('Name:', name)

            onboardServiceC = fDetails.select_one('.tabel-ferry-build') # typo is in site
            
            buildStats = dict()
            buildStatItems = fDetails.select_one('.ferrydetails-build-statistics'
                ).select('li[class="list-group-item"]')
            for item in buildStatItems:
                buildStatKey = item.select_one('.information-data').getText(strip=True).upper()
                buildStatVal = item.select_one('.information-value').getText(strip=True).upper()
                buildStats[buildStatKey] = buildStatVal
            print('Build stats:', buildStats)

            services = []
            for item in onboardServiceC.find('ul').find_all('img'):
                amenityImgSrc = urlparse(ujson.loads(item['data-media'])["1"]).path
                services.append(service(settings.SCRAPER_AMENITY_IMAGE_PATHS.get(amenityImgSrc, amenityImgSrc), False))

            for item in onboardServiceC.select('.ferrydetails-onboard-sec'):
                services.append(service(item.select_one('.col-lg-10').getText(strip=True), True))
            print('Services:', services)

            m.Ship.objects.filter(code=code).delete()

            ship = m.Ship(
                code = code,
                name = name,
                car_capacity = int(buildStats.get('CAR CAPACITY', 0)),
                human_capacity = int(buildStats.get('PASSENGER & CREW CAPACITY', 0)),
                horsepower = int(buildStats.get('HORSEPOWER', 0)),
                max_displacement = float(buildStats.get('MAXIMUM DISPLACEMENT (T)', 0)),
                max_speed = float(buildStats.get('MAXIMUM SPEED (KNOTS)', 0)),
                total_length = float(buildStats.get('OVERALL LENGTH (M)', 0)),
            )

            built = buildStats.get('BUILT', '').split(',')
            for builtVal in built:
                try:
                    ship.built = date(int(builtVal), 1, 1)
                    print('Built:', ship.built)
                    break
                except ValueError as e:
                    print(e)
            
            ship.save()

            for newService in services:
                ship.services.add(newService)

            print('Created ship', ship)
            print('\n')

            #   sleep(settings.SCRAPER_PAUSE_SECS)
            #   fModal = bs(
            #   requests.get(settings.SCRAPER_URL_PREFIX+'/ship-info', {'code': ship.code}).json()['shipInfoModalHtml'],
            #       'html.parser')
