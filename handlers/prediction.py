import logging
import face_recognition
import numpy as np
import dlib

from aiohttp.web_response import Response
from aiohttp_apispec import docs, response_schema

from PIL import Image
from io import BytesIO

from .base import BaseView
from message_schema import PredictImageResp

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

log.setLevel(logging.DEBUG)

face_detector = dlib.get_frontal_face_detector()


class PredictionHandler(BaseView):
    URL_PATH = r'/check_similarity/{threshold}/{n}/'

    @property
    def threshold(self):
        return str(self.request.match_info.get('threshold'))

    @property
    def n(self):
        return int(self.request.match_info.get('n'))

    @docs(summary="Предикт по фото", tags=["Basic methods"],
          description="Классификация входящего изображения. "
                      "Выводит самые похожие фотки по евклидово расстоянию",
          parameters=[
              {
                  'in': 'path',
                  'name': 'n',
                  'schema': {'type': 'string', 'format': 'uuid'},
                  'required': 'true',
                  'description': 'Кол-во наиболее близких соседей'
              }
          ]
          )
    @response_schema(PredictImageResp(), description="")
    async def post(self):
        try:
            reader = await self.request.multipart()
            # /!\ Don't forget to validate your inputs /!\
            image = await reader.next()
            # TODO отвалидировать ответ
            if not image.filename.endswith("jpg"):
                return Response(body={"MESSAGE_NAME": "PREDICT_PHOTO",
                                      "STATUS": False,
                                      "PAYLOAD": {
                                          "result": None,
                                          "description": "wrong file format, try loading a different format"
                                      }})

            arr = []
            while True:
                chunk = await image.read_chunk()  # 8192 bytes by default.
                if not chunk:
                    break
                arr.append(chunk)
            img_arr = np.array(Image.open(BytesIO(b"".join(arr))))
            detected_faces = face_detector(img_arr, 1)
            if len(detected_faces) > 0:
                # TODO используем первое попавшееся лицо в кадре(в дальнейшем нужно изменить)
                face_rect = detected_faces[0]
                crop = img_arr[face_rect.top():face_rect.bottom(), face_rect.left():face_rect.right()]
                # threshold = 0.7
                encodings = face_recognition.face_encodings(crop)
                if len(encodings) > 0:
                    query = "SELECT file FROM vectors WHERE sqrt(power(CUBE(array[{}]) <-> vec_low, 2) + power(CUBE(array[{}]) <-> vec_high, 2)) <= {} ".format(
                        ','.join(str(s) for s in encodings[0][0:64]),
                        ','.join(str(s) for s in encodings[0][64:128]),
                        self.threshold,
                    ) + \
                              "ORDER BY sqrt(power(CUBE(array[{}]) <-> vec_low, 2) + power(CUBE(array[{}]) <-> vec_high, 2)) ASC LIMIT 10".format(
                                  ','.join(str(s) for s in encodings[0][0:64]),
                                  ','.join(str(s) for s in encodings[0][64:128]),
                              )
                    result = []
                    for row in await self.pg.fetch(query):
                        a = row['file']
                        result.append(a)
                    if len(result) > 0:
                        return Response(body={
                            "MESSAGE_NAME": "PREDICT_PHOTO",
                            "STATUS": True,
                            "PAYLOAD": {
                                "threshold": self.threshold,
                                "result": [x.split("_")[0] for x in result][:self.n],
                                "description": "OK"
                            }})
                    else:
                        return Response(body={
                            "MESSAGE_NAME": "PREDICT_PHOTO",
                            "STATUS": False,
                            "PAYLOAD": {
                                "threshold": self.threshold,
                                "result": None,
                                "description": "NOTHING FOUND in DB"
                            }})
                else:
                    logging.info("handler name - %r, message_name - %r, error decoding - %r",
                                 "PredictionHandler", "PREDICT_PHOTO", "face recognition library not find face")
                    return Response(body={
                        "MESSAGE_NAME": "PREDICT_PHOTO",
                        "STATUS": False,
                        "PAYLOAD": {
                            "result": None,
                            "description": "NO FACE"
                        }})
            else:
                logging.info("handler name - %r, message_name - %r, error decoding - %r",
                             "PredictionHandler", "PREDICT_PHOTO", "hog detector not find face")
                return Response(body={
                    "MESSAGE_NAME": "PREDICT_PHOTO",
                    "STATUS": False,
                    "PAYLOAD": {
                        "result": None,
                        "description": "NO FACE"
                    }})

                # TODO обращаемся к базе и сравниваем вектора

        except Exception as e:
            logging.info("handler name - %r, message_name - %r, error - %r",
                         "PredictionHandler", "PREDICT_PHOTO", e)
            return Response(body={
                "MESSAGE_NAME": "PREDICT_PHOTO",
                "STATUS": False,
                "PAYLOAD": {
                    "result": None,
                    "description": "unexpected runtime error"
                }
            })
