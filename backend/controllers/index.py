from typing import cast, Optional
from pypika.terms import AggregateFunction
from tortoise.expressions import Aggregate
from starlite import Router, get, post
from tortoise.expressions import Q
from tortoise.functions import Min
from html import unescape as ue
import json
from tortoise import Tortoise

from monitor_match import match_monitors_to_postings


from models import Monitor, MonitorPosting, EShop

class BoolOrF(AggregateFunction):
    def __init__(self, term, alias=None):
        super(BoolOrF, self).__init__("BOOL_OR", term, alias=alias)

class BoolOr(Aggregate):
    """
    Returns smallest value in the column.

    :samp:`Min("{FIELD_NAME}")`
    """

    database_func = BoolOrF
    populate_field_object = True

@get("/")
async def list_monitors(
    offset: int = 0,
    limit: int = 50,
    name: Optional[str] = None,
    price_from: Optional[int] = None,
    price_to: Optional[int] = None,
    in_stock: Optional[bool] = None,
) -> list[Monitor]:

    monitor_filters = {}
    if name:
        monitor_filters["name__icontains"] = name

    postings_filters = {}
    if price_from:
        postings_filters["min_price__gte"] = price_from
    if price_to:
        postings_filters["min_price__lte"] = price_to
    if in_stock is not None:
        postings_filters["in_stock"] = in_stock

    result = (
        Monitor.filter(
            Q(
                **monitor_filters
                # equivalent to:
                # Q(monitor__name__icontains=name),
            )
        )
        .prefetch_related("posts")
        # .annotate(min_price=Min("postings__price"))
        # .annotate(in_stock=BoolOr("postings__in_stock"))
        .filter(
            Q(
                **postings_filters
                # equivalent to:
                # Q(min_price__gte=price_from),
                # Q(min_price__lte=price_to),
                # Q(in_stock=in_stock),
            )
        )
        .offset(offset)
        .limit(limit)
    )

    return result


@post("/dummy_monitors")
async def list_monitors_dummy() -> list[Monitor]:
    return cast("list[Monitor]", [{"name": "DELL MONITOR 24\" U2422HE", "price": "638,00", "url": "/dell-monitor-24-u2422he/art_109244/"}])

@post("/import_json")
async def import_json() -> str:
    eshop = await EShop.create(name='dummy')
    monitors = match_monitors_to_postings()
    print(monitors)
    monitores_importados = 0
    for index, monitor in enumerate(monitors):
        name = monitor['name']
        brand = monitor['brand']
        size = monitor['size']
        panel = monitor['panel']
        refresh_rate = monitor['refresh_rate']
        min_response_time = monitor['min_response_time']
        screen_aspect_ratio = monitor['screen_aspect_ratio']
        screen_resolution = monitor['screen_resolution']
        url = monitor['url']
        # print(name,brand,size,panel,refresh_rate,min_response_time,screen_aspect_ratio,screen_resolution,url)
        created_monitor = await Monitor.create(name=name, brand=brand, size=size, panel=panel, refresh_rate=refresh_rate, min_response_time=min_response_time, screen_aspect_ratio=screen_aspect_ratio, screen_resolution=screen_resolution, url=url)
        for posting in monitor['postings']:
            await MonitorPosting.create(monitor=created_monitor, price=999, in_stock=posting['stock'], eshop=eshop)
        monitores_importados += 1

    return f"Se realizo el buen import de {monitores_importados} monitores"


index_router = Router(path="/", route_handlers=[list_monitors, list_monitors_dummy, import_json])
