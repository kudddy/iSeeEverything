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
from localdb import uid_to_table_mapping, model

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

log.setLevel(logging.DEBUG)

face_detector = dlib.get_frontal_face_detector()

size = (720, 720)

import time


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
            print("---загрузка фото---")
            start_time = time.time()
            reader = await self.request.multipart()
            # /!\ Don't forget to validate your inputs /!\
            image = await reader.next()
            arr = []
            while True:
                chunk = await image.read_chunk()  # 8192 bytes by default.
                if not chunk:
                    break
                arr.append(chunk)
            print("--- %s seconds ---" % (time.time() - start_time))
            try:
                print("---Image.open---")
                start_time = time.time()
                # оригинал
                img = Image.open(BytesIO(b"".join(arr)))
                print("--- %s seconds ---" % (time.time() - start_time))

                if img.format == "PNG":
                    img_frm: str = "png"
                elif img.format == "JPEG":
                    img_frm: str = "jpeg"
                else:
                    return Response(body={"MESSAGE_NAME": "PREDICT_PHOTO",
                                          "STATUS": False,
                                          "PAYLOAD": {
                                              "result": None,
                                              "description": "wrong file format, try loading a different format"
                                          }})

                # решение проблемы с iphone photo
                print("---img.getexif---")
                start_time = time.time()
                exif = img.getexif()
                print("--- %s seconds ---" % (time.time() - start_time))
                print(exif)
                if len(exif) > 0:
                    print("---ImageOps.exif_transpose---")
                    start_time = time.time()
                    img = ImageOps.exif_transpose(img)
                    print("--- %s seconds ---" % (time.time() - start_time))
                    print("---Перезапись---")
                    b = BytesIO()
                    img.save(b, format=img_frm)
                    img = Image.open(b)
                    print("--- %s seconds ---" % (time.time() - start_time))


                # режем слишком большие изображения
                print("---img.thumbnail---")
                start_time = time.time()
                if img.size[0] > 1000 or img.size[1] > 1000:
                    img.thumbnail(size)
                print("--- %s seconds ---" % (time.time() - start_time))

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
            print("---конвертация---")
            start_time = time.time()
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
            print("--- %s seconds ---" % (time.time() - start_time))
            print("---face_detector---")
            start_time = time.time()
            detected_faces = face_detector(img_arr, 1)
            print("--- %s seconds ---" % (time.time() - start_time))
            if len(detected_faces) > 0:
                # TODO используем первое попавшееся лицо в кадре(в дальнейшем нужно изменить)
                print("---обрезка и декодирование фото---")
                start_time = time.time()
                face_rect = detected_faces[0]
                crop = img_arr[face_rect.top():face_rect.bottom(), face_rect.left():face_rect.right()]
                encodings = face_recognition.face_encodings(crop)
                print("--- %s seconds ---" % (time.time() - start_time))

                # kmeans кластеризация призванная уменьшить время расчета евклидова расстояния
                print("---кластеризация---")
                start_time = time.time()
                cluster: int = model.predict([encodings[0]])[0]
                print("--- %s seconds ---" % (time.time() - start_time))

                if len(encodings) > 0:
                    print("---селект в базу---")
                    start_time = time.time()
                    query = "SELECT file FROM {} WHERE clusters = {} AND sqrt(power(CUBE(array[{}]) <-> vec_low, 2) + power(CUBE(array[{}]) <-> vec_high, 2)) <= {} ".format(
                        uid_to_table_mapping[self.uid],
                        cluster,
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
                    print("--- %s seconds ---" % (time.time() - start_time))
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
