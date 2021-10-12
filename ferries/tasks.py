from celery import shared_task
from .models import RouteInfo, Route
from scripts import (
    save_sitemap,
    scrape_routes,
    scrape_fleet,
    scrape_schedule,
    scrape_current_conditions,
)

@shared_task
def save_sitemap_task():
    save_sitemap.run()
    return True

@shared_task
def scrape_schedule_task():
    scrape_schedule.run()
    return True

@shared_task
def scrape_routes_task():
    scrape_routes.run()
    return True

@shared_task
def scrape_fleet_task():
    scrape_fleet.run()
    return True

@shared_task
def scrape_ferry_task(url):
    return scrape_fleet.scrape_ferry(url)

@shared_task
def scrape_route_schedule_task(route_pk):
    route = Route.objects.get(pk=route_pk)
    scrape_schedule.init_misc_schedules()
    scrape_schedule.scrape_route(route)
    return True

@shared_task
def scrape_current_conditions_task():
    save_sitemap.run()
    return True

@shared_task
def scrape_route_current_conditions_task(route_info_pk):
    route_info = RouteInfo.objects.get(pk=route_info_pk)
    scrape_current_conditions.scrape_conditions_tables()
    scrape_current_conditions.get_current_sailings(route_info)
    return True