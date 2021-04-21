import logging

from aiohttp.web_response import Response
from aiohttp_apispec import docs, response_schema
from sqlalchemy import select
from db.schema import comments

from .base import BaseView
from message_schema import GetCommentResp

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

log.setLevel(logging.DEBUG)


class GetCommentHandler(BaseView):
    URL_PATH = r'/getcomments/'

    @docs(summary="Возвращает Комментарии к фото", tags=["Basic methods"],
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
                  'name': 'PAYLOAD',
                  'schema': {'type': 'dict', 'format': 'url:url'},
                  'required': 'true',
                  'description': 'url to photo'
              }
          ]
          )
    @response_schema(GetCommentResp(), description="Возвращаем ранее добавлены комментарии к фотографии, "
                                                   "сортированные по дате")
    async def post(self):
        status: bool = True
        result: list = []
        try:
            res: dict = await self.request.json()
            payload: dict = res["PAYLOAD"]

            query = select([comments.c.comment]).where(comments.c.file == payload["url"])
            for row in await self.pg.fetch(query):
                result.append(row['comment'])

            logging.info("handler name - %r, message_name - %r, info - %r",
                         "GetCommentHandler", "GET_COMMENT", "OK")

        except Exception as e:
            status = False
            logging.info("handler name - %r, message_name - %r, info - %r, error - %r",
                         "GetCommentHandler", "GET_COMMENT", "FAIL", e)

        return Response(body={"MESSAGE_NAME": "GET_COMMENT",
                              "STATUS": status,
                              "PAYLOAD": {
                                  "result": result,
                                  "description": "OK"
                              }})
