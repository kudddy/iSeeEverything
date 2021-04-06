import logging
import face_recognition
import numpy as np
import dlib

from aiohttp.web_response import Response
from aiohttp_apispec import docs, response_schema

from PIL import Image, ImageOps
from io import BytesIO

from .base import BaseView
from message_schema import PredictImageResp
from localdb import uid_to_table_mapping

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

log.setLevel(logging.DEBUG)

face_detector = dlib.get_frontal_face_detector()


class PredictionHandler(BaseView):
    URL_PATH = r'/check_similarity/{uid}/{threshold}/{n}/'

    @property
    def threshold(self):
        return str(self.request.match_info.get('threshold'))

    @property
    def n(self):
        return int(self.request.match_info.get('n'))

    @property
    def uid(self):
        return str(self.request.match_info.get('uid'))

    @docs(summary="Предикт по фото", tags=["Basic methods"],
          description="Классификация входящего изображения. "
                      "Выводит самые похожие фотки по евклидово расстоянию",
          parameters=[
              {
                  'in': 'path',
                  'name': 'uid',
                  'schema': {'type': 'string', 'format': 'uuid'},
                  'required': 'true',
                  'description': 'model unique id'
              },
              {
                  'in': 'path',
                  'name': 'threshold',
                  'schema': {'type': 'string', 'format': 'uuid'},
                  'required': 'true',
                  'description': 'threshold'
              },
              {
                  'in': 'path',
                  'name': 'n',
                  'schema': {'type': 'string', 'format': 'uuid'},
                  'required': 'true',
                  'description': 'Number of closest neighbors'
              }
          ]
          )
    @response_schema(PredictImageResp(), description="")
    async def post(self):
        try:
            if self.uid not in uid_to_table_mapping:
                logging.info("handler name - %r, message_name - %r info - %r",
                             "PredictionHandler", "PREDICT_PHOTO", "unknown uid")

                return Response(body={"MESSAGE_NAME": "PREDICT_PHOTO",
                                      "STATUS": False,
                                      "PAYLOAD": {
                                          "result": None,
                                          "description": "unknown uid"
                                      }})

            reader = await self.request.multipart()
            # /!\ Don't forget to validate your inputs /!\
            image = await reader.next()
            arr = []
            while True:
                chunk = await image.read_chunk()  # 8192 bytes by default.
                if not chunk:
                    break
                arr.append(chunk)

            try:
                # оригинал
                img = Image.open(BytesIO(b"".join(arr)))
                # решение проблемы с iphone photo
                exif = img.getexif()
                if len(exif) > 0:
                    img = ImageOps.exif_transpose(img)
                    b = BytesIO()
                    img.save(b, format="jpeg")
                    img = Image.open(b)

            except Exception as e:
                logging.info("handler name - %r, message_name - %r, error - %r, info - %r",
                             "PredictionHandler", "PREDICT_PHOTO", e, "its not image")

                return Response(body={"MESSAGE_NAME": "PREDICT_PHOTO",
                                      "STATUS": False,
                                      "PAYLOAD": {
                                          "result": None,
                                          "description": "its not image"
                                      }})
            # проверка типа изображения

            if img.format == "PNG":
                img_arr = np.array(img.convert('RGB'))
            elif img.format == "JPEG":
                img_arr = np.array(img)
            else:
                return Response(body={"MESSAGE_NAME": "PREDICT_PHOTO",
                                      "STATUS": False,
                                      "PAYLOAD": {
                                          "result": None,
                                          "description": "wrong file format, try loading a different format"
                                      }})

            detected_faces = face_detector(img_arr, 1)
            if len(detected_faces) > 0:
                # TODO используем первое попавшееся лицо в кадре(в дальнейшем нужно изменить)
                face_rect = detected_faces[0]
                crop = img_arr[face_rect.top():face_rect.bottom(), face_rect.left():face_rect.right()]
                encodings = face_recognition.face_encodings(crop)
                if len(encodings) > 0:
                    query = "SELECT file FROM {} WHERE sqrt(power(CUBE(array[{}]) <-> vec_low, 2) + power(CUBE(array[{}]) <-> vec_high, 2)) <= {} ".format(
                        uid_to_table_mapping[self.uid],
                        ','.join(str(s) for s in encodings[0][0:64]),
                        ','.join(str(s) for s in encodings[0][64:128]),
                        self.threshold,
                    ) + \
                            "ORDER BY sqrt(power(CUBE(array[{}]) <-> vec_low, 2) + power(CUBE(array[{}]) <-> vec_high, 2)) ASC LIMIT {}".format(
                                ','.join(str(s) for s in encodings[0][0:64]),
                                ','.join(str(s) for s in encodings[0][64:128]),
                                self.n
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
