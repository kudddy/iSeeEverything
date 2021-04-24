import logging

from aiohttp.web_response import Response
from aiohttp_apispec import docs, response_schema
from sqlalchemy import select, func, desc
from db.schema import comments

from .base import BaseView
from message_schema import PredictImageResp

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

log.setLevel(logging.DEBUG)


class GetTopComment(BaseView):
    URL_PATH = r'/gettopcomments/'

    @docs(summary="Возвращает топ фотографии по кол-ву комментариев", tags=["Basic methods"],
          description="Ручка возвращает топ фотографии по кол-ву комментариев",
          )
    @response_schema(PredictImageResp(), description="Возвращаем ранее добавлены комментарии к фотографии, "
                                                     "сортированные по дате")
    async def post(self):
        status: bool = True
        result: list = []
        try:

            query = select([comments.c.file, func.count(comments.c.file).label('count')]) \
                .group_by(comments.c.file) \
                .order_by(desc('count'))

            for row in await self.pg.fetch(query):
                result.append(row['file'])

            logging.info("handler name - %r, message_name - %r, info - %r",
                         "GetTopComment", "GET_TOP_COMMENT", "OK")

        except Exception as e:
            status = False
            logging.info("handler name - %r, message_name - %r, info - %r, error - %r",
                         "GetTopComment", "GET_TOP_COMMENT", "FAIL", e)

        return Response(body={"MESSAGE_NAME": "GET_TOP_COMMENT",
                              "STATUS": status,
                              "PAYLOAD": {
                                  "result": result,
                                  "description": "OK"
                              }})
