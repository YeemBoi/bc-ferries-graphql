from django.conf import settings
from django.utils.module_loading import import_string
from time import sleep

for scraper_script_str in settings.SCRAPER['INIT_SCRIPTS']:
    print('Running script', scraper_script_str)
    sleep(settings.SCRAPER['PAUSE_SECS'])
    import_string(f"scripts.{scraper_script_str}.run")()
    print('\n')
