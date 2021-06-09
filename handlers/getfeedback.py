import logging

from aiohttp.web_response import Response
from aiohttp_apispec import docs, response_schema
from sqlalchemy import select, desc
from db.schema import feedback

from .base import BaseView
from message_schema import GetCommentResp

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

log.setLevel(logging.DEBUG)


class GetFeedBackHandler(BaseView):
    URL_PATH = r'/getfeedback/'

    @docs(summary="Возвращает отзывы, которые добавили пользователи", tags=["Basic methods"],
          description="Ручка возвращает ранее добавлены отзывы о сайте",
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
    @response_schema(GetCommentResp(), description="Возвращаем ранее добавлены отзывы к сайту, "
                                                   "сортированные по дате")
    async def post(self):
        status: bool = True
        result: list = []
        try:
            query = select([feedback.c.comment]).order_by(desc(feedback.c.date))
            for row in await self.pg.fetch(query):
                result.append(row['comment'])

            logging.info("handler name - %r, message_name - %r, info - %r",
                         "GetCommentHandler", "GET_FEEDBACK", "OK")
        except Exception as e:
            status = False
            logging.info("handler name - %r, message_name - %r, info - %r, error - %r",
                         "GetCommentHandler", "GET_FEEDBACK", "FAIL", e)
        return Response(body={"MESSAGE_NAME": "GET_FEEDBACK",
                              "STATUS": status,
                              "PAYLOAD": {
                                  "result": result[:8],
                                  "description": "OK"
                              }})
