#!/usr/bin/python3

import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ferries.settings')

import django
django.setup()

import html5lib
import ujson

from datetime import date

import requests
from urllib.parse import urlparse
from time import sleep
import core.models as m

from bs4 import BeautifulSoup as bs

FLEET_PAGE_RANGE = 2
PAUSE_SECS = 10

URL_PREFIX = 'http://www.bcferries.com'

# BC Ferries doesn't use alt tags on all images, so map image src to amenities
AMENITY_IMAGE_PATHS = {
    '/web_image/h8e/h8d/8800764362782.jpg': 'Arbutus Coffee Bar',
    '/web_image/h81/h88/8798826168350.jpg': 'Aurora Lounge',
    '/web_image/h03/h6d/8798746312734.jpg': 'Canoe Cafe',
    '/web_image/h41/hd5/8798823022622.jpg': 'Coast Cafe Express',
    '/web_image/hcb/hd0/8798832164894.jpg': 'Coastal Cafe',
    '/web_image/h9d/h69/8800604258334.jpg': 'Pacific Buffet',
    '/web_image/haa/hf3/8800605044766.jpg': 'Passages',
    '/web_image/h20/h0b/8798760566814.jpg': 'SeaWest Lounge',
    '/web_image/h44/h77/8798814371870.jpg': 'Sitka Coffee Place',
    '/web_image/hf7/hb3/8798767808542.jpg': 'The Raven Lounge',
    '/web_image/h6a/h96/8798810800158.jpg': 'Vista Restaurant',
}

def service(name: str, is_additional: bool) -> m.Service:
    amenity, created = m.Service.objects.get_or_create(name=name, is_additional=is_additional)
    if created:
        print('created service', amenity)
    return amenity

def main():
    for n in range(FLEET_PAGE_RANGE):
        sleep(PAUSE_SECS)
        req = requests.get(URL_PREFIX+'/on-the-ferry/our-fleet', {'page': n})
        req.encoding = req.apparent_encoding
        soup = bs(req.text ,'html5lib')
        for bx in soup.select('div[class="ferry-bx"]'):
            href = bx.find('a')['href']
            print('Found ferry url', href)
            sleep(PAUSE_SECS)
            fReq = requests.get(URL_PREFIX+href)
            fReq.encoding = fReq.apparent_encoding
            fPage = bs(fReq.text ,'html5lib')
            fDetails = fPage.select_one('.ferrydetails-accordion-sec')
            fMain = fPage.find('div', id='ferryDetails')
            code = list(filter(None, urlparse(href).path.split('/')))[-1]
            print('code:', code)
            name = fMain.find('h3').find('strong').getText(strip=True)
            print('name:', name)

            onboardServiceC = fDetails.select_one('.tabel-ferry-build') # typo is in site
            
            buildStats = dict()
            buildStatItems = fDetails.select_one('.ferrydetails-build-statistics'
                ).select('li[class="list-group-item"]')
            for item in buildStatItems:
                buildStatKey = item.select_one('.information-data').getText(strip=True).upper()
                buildStatVal = item.select_one('.information-value').getText(strip=True).upper()
                buildStats[buildStatKey] = buildStatVal
            print('build stats:', buildStats)

            services = []
            for item in onboardServiceC.find('ul').find_all('img'):
                amenityImgSrc = urlparse(ujson.loads(item['data-media'])["1"]).path
                services.append(service(AMENITY_IMAGE_PATHS.get(amenityImgSrc, amenityImgSrc), False))

            for item in onboardServiceC.select('.ferrydetails-onboard-sec'):
                services.append(service(item.select_one('.col-lg-10').getText(strip=True), True))
            print('services:', services)

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
                    print('built:', ship.built)
                    break
                except ValueError as e:
                    print(e)
            
            ship.save()

            for newService in services:
                ship.services.add(newService)

            print('created ship', ship)
            print('\n')

            #   sleep(PAUSE_SECS)
            #   fModal = bs(
            #   requests.get(URL_PREFIX+'/ship-info', {'code': ship.code}).json()['shipInfoModalHtml'],
            #       'html.parser')
            

if __name__ == '__main__':
    main()
