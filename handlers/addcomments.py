import logging
from datetime import datetime

from aiohttp.web_response import Response
from aiohttp_apispec import docs, response_schema
from db.schema import comments

from .base import BaseView
from message_schema import AddCommentResp

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

log.setLevel(logging.DEBUG)


class AddCommentHandler(BaseView):
    URL_PATH = r'/addcomments/'

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
    @response_schema(AddCommentResp(), description="Добавляем комментарии к фотографии")
    async def post(self):
        status: bool = True
        try:
            res: dict = await self.request.json()

            payload: dict = res["PAYLOAD"]

            logging.info("handler name - %r, message_name - %r, info - %r",
                         "AddCommentHandler", "ADD_COMMENT", "OK")

            # запрос к db на добавление комментария в бд(id, url фото, комментарий, дата)

            query = comments.insert().values(file=payload["url"], comment=payload["comment"], date=datetime.now())

            await self.pg.fetch(query)

        except Exception as e:
            status = False
            logging.info("handler name - %r, message_name - %r, info - %r, error - %r",
                         "AddCommentHandler", "ADD_COMMENT", "FAIL", e)

        return Response(body={"MESSAGE_NAME": "ADD_COMMENT",
                              "STATUS": status,
                              })



