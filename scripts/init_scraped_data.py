from django.conf import settings
from django.utils.module_loading import import_string
from time import sleep

for scraper_script_str in settings.SCRAPER_SCRIPTS:
    scraper_script_run = import_string('scripts.' + scraper_script_str + '.run')
    print('Running script', scraper_script_str)
    sleep(settings.SCRAPER_PAUSE_SECS)
    scraper_script_run()
    print('\n')
