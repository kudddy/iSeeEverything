import logging

from aiohttp.web_response import Response
from aiohttp_apispec import docs, response_schema

from .base import BaseView
from message_schema import GetCommentResp

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

log.setLevel(logging.DEBUG)


class GetCommentHandler(BaseView):
    URL_PATH = r'/getcomments/'

    @docs(summary="Комментарии к фото", tags=["Basic methods"],
          description="Ручка возвращает ранее добавлены комментарии к фотографии",
          parameters=[
              {
                  'in': 'json',
                  'name': 'MESSAGE_NAME',
                  'schema': {'type': 'string', 'format': 'string'},
                  'required': 'true',
                  'description': 'message name'
              },
              {
                  'in': 'json',
                  'name': 'url',
                  'schema': {'type': 'string', 'format': 'uuid'},
                  'required': 'true',
                  'description': 'url to photo'
              }
          ]
          )
    @response_schema(GetCommentResp(), description="Возвращаем ранее добавлены комментарии к фотографии, "
                                                   "сортированные по дате")
    async def post(self):

        res = await self.request.json()
        print(res)
        logging.info("handler name - %r, message_name - %r, info - %r",
                     "GetCommentHandler", "GET_COMMENT", "OK")

        return Response(body={"MESSAGE_NAME": "GET_COMMENT",
                              "STATUS": True,
                              "PAYLOAD": {
                                  "result": ["Шлюха", "Ебал ее как то раз"],
                                  "description": "OK"
                              }})
