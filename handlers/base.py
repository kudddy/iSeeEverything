from aiohttp.web_urldispatcher import View
from asyncpgsa import PG
# aiohttp_cors.WebViewMixig

from aiohttp_cors import CorsViewMixin


class BaseView(View, CorsViewMixin):
    URL_PATH: str

    @property
    def pg(self) -> PG:
        return self.request.app['pg']

    @property
    def cache(self):
        return self.request.app['cache']

    @property
    def encoders(self):
        return self.request.app['encoders']
