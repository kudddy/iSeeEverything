import logging
from os import listdir
from os.path import join

from types import AsyncGeneratorType, MappingProxyType
from typing import AsyncIterable, Mapping

from aiohttp import PAYLOAD_REGISTRY
from aiohttp.web_app import Application
from aiohttp_apispec import setup_aiohttp_apispec, validation_middleware
import aiohttp_cors
from concurrent.futures.process import ProcessPoolExecutor

# import aiomcache
# import asyncio

from handlers import HANDLERS
# from middleware import error_middleware, handle_validation_error, check_token_middleware
from payloads import AsyncGenJSONListPayload, JsonPayload
from utils.pg import setup_pg

# from helper import Pickler, check_folder_in_path
#
# from facedecoder.manager import run_model_updater
# from db.schema import done_encoders

api_address = "0.0.0.0"
api_port = 8081

MEGABYTE = 1024 ** 2
MAX_REQUEST_SIZE = 70 * MEGABYTE

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

log.setLevel(logging.DEBUG)


def create_app() -> Application:
    """
    Создает экземпляр приложения, готового к запуску
    """
    # TODO добавить middlewares для вадидации полей сообщений
    app = Application(
        client_max_size=MAX_REQUEST_SIZE,
        # middlewares=[check_token_middleware]
    )
    aiohttp_cors.setup(app, defaults={
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
        )
    })
    app.cleanup_ctx.append(setup_pg)



    # route = cors.add(
    #     resource.add_route("GET", handler), {
    #         "http://client.example.org": aiohttp_cors.ResourceOptions(
    #             allow_credentials=True,
    #             expose_headers=("X-Custom-Server-Header",),
    #             allow_headers=("X-Requested-With", "Content-Type"),
    #             max_age=3600,
    #         )
    #     })

    # app.on_startup.append(startup)
    # app.on_shutdown.append(shutdown)

    # # регестрируем менеджер кеша
    # app['cache'] = CacheManager()
    # app['encoders'] = EncoderManager()

    # Регистрация обработчика
    for handler in HANDLERS:
        log.debug('Registering handler %r as %r', handler, handler.URL_PATH)

        route = app.router.add_route('*', handler.URL_PATH, handler)

        app['aiohttp_cors'].add(route)

    setup_aiohttp_apispec(app=app, title="GROUP BY FACE API", swagger_path='/')

    # Автоматическая сериализация в json данных в HTTP ответах
    PAYLOAD_REGISTRY.register(AsyncGenJSONListPayload,
                              (AsyncGeneratorType, AsyncIterable))
    PAYLOAD_REGISTRY.register(JsonPayload, (Mapping, MappingProxyType))
    return app
