from ferries import models as m

from common.scraper_utils import get_url, request_soup, soft_print_iter, clean_tag_text, SCRAPER_SETTINGS
from urllib.parse import urlparse
from datetime import date
import ujson

def service(name: str, is_additional: bool) -> m.Service:
    amenity, created = m.Service.objects.get_or_create(name=name, is_additional=is_additional)
    if created: print('Created service', amenity)
    return amenity

def _built_date(data = None):
    if not data: return None
    for built_val in data.split(','):
        try: return date(int(built_val), 1, 1)
        except ValueError as e: print(e)

BUILD_STATS = [
    ('car_capacity', 'CAR CAPACITY', int),
    ('human_capacity', 'PASSENGER & CREW CAPACITY', int),
    ('horsepower', 'HORSEPOWER', int),
    ('max_displacement', 'MAXIMUM DISPLACEMENT (T)', float),
    ('max_speed', 'MAXIMUM SPEED (KNOTS)', float),
    ('total_length', 'OVERALL LENGTH (M)', float),
    ('built', 'BUILT', _built_date),
]
AMENITY_IMAGE_PATHS = {
    '/web_image/h8e/h8d/8800764362782.jpg':'Arbutus Coffee Bar',
    '/web_image/h81/h88/8798826168350.jpg':'Aurora Lounge',
    '/web_image/h03/h6d/8798746312734.jpg':'Canoe Cafe',
    '/web_image/h41/hd5/8798823022622.jpg':'Coast Cafe Express',
    '/web_image/hcb/hd0/8798832164894.jpg':'Coastal Cafe',
    '/web_image/h9d/h69/8800604258334.jpg':'Pacific Buffet',
    '/web_image/haa/hf3/8800605044766.jpg':'Passages',
    '/web_image/h20/h0b/8798760566814.jpg':'SeaWest Lounge',
    '/web_image/h44/h77/8798814371870.jpg':'Sitka Coffee Place',
    '/web_image/hf7/hb3/8798767808542.jpg':'The Raven Lounge',
}

def scrape_ferry(url: str) -> m.Ferry:
    soup = request_soup(url)
    f_details = soup.select_one('.ferrydetails-accordion-sec')
    f_main = soup.find('div', id='ferryDetails')
    code = list(filter(None, urlparse(url).path.split('/')))[-1]
    print('Code:', code)
    attrs = {
        'name': f_main.find('h3').find('strong').get_text(strip=True),
        'official_page': url,
    }
    build_stats = {
        clean_tag_text(item.select_one('.information-data')):
        item.select_one('.information-value').get_text(strip=True)
        for item in f_details.select_one('.ferrydetails-build-statistics').select('li[class="list-group-item"]')
    }
    attrs.update({
        attr_name: clean_func(build_stats.get(find_text, clean_func()))
        for attr_name, find_text, clean_func in BUILD_STATS
    })
    onboard_service_c = f_details.select_one('.tabel-ferry-build') # typo is in site  
    services = [
        service(item.select_one('.col-lg-10').get_text(strip=True), True)
        for item in onboard_service_c.select('.ferrydetails-onboard-sec')
    ]
    for item in onboard_service_c.find('ul').select('img'):
        amenityImgSrc = urlparse(ujson.loads(item['data-media'])["1"]).path
        services.append(service(AMENITY_IMAGE_PATHS.get(amenityImgSrc, amenityImgSrc), False))
    soft_print_iter('Services:', services)
    print('Attributes:')
    for key, val in attrs.items():
        print(f"{key}: {val}")
    ferry, created = m.Ferry.objects.update_or_create(code=code, defaults=attrs)
    ferry.services.set(services)
    if created: print('Created ferry', ferry)
    return ferry


def run():
    for n in range(SCRAPER_SETTINGS.FLEET_PAGE_RANGE):
        soup = request_soup(get_url('FLEET').format(n))
        for bx in soup.select('div[class="ferry-bx"]'):
            scrape_ferry(SCRAPER_SETTINGS.URL_PREFIX + bx.find('a')['href'])
            print('\n')
