import logging
from datetime import datetime

from aiohttp.web_response import Response
from aiohttp_apispec import docs, response_schema
from db.schema import feedback

from .base import BaseView
from message_schema import AddCommentResp

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

log.setLevel(logging.DEBUG)


class AddFeedbackHandler(BaseView):
    URL_PATH = r'/addfeedback/'

    @docs(summary="Добавление отзыва по нажатию кнопки", tags=["Basic methods"],
          description="Ручка добавляет отзыв пользователя о сайте",
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
    @response_schema(AddCommentResp(), description="Пишем в базу отзыв клиентов")
    async def post(self):
        status: bool = True
        try:
            res: dict = await self.request.json()

            payload: dict = res["PAYLOAD"]

            # запрос к db на добавление комментария в бд(id, url фото, комментарий, дата)

            query = feedback.insert().values(
                comment=payload["comment"],
                date=datetime.now()
            )

            await self.pg.fetch(query)

            logging.info("handler name - %r, message_name - %r, info - %r",
                         "AddCommentHandler", "ADD_FEEDBACK", "OK")

        except Exception as e:
            status = False
            logging.info("handler name - %r, message_name - %r, info - %r, error - %r",
                         "AddCommentHandler", "ADD_FEEDBACK", "FAIL", e)

        return Response(body={
            "MESSAGE_NAME": "ADD_FEEDBACK",
            "STATUS": status
        })
