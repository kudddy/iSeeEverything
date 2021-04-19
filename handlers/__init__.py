from .prediction import PredictionHandler
from .getcomments import GetCommentHandler
from .addcomments import AddCommentHandler

# HANDLERS = (CheckToken, CreateToken, UploadFile, PredictionHandler)


HANDLERS = (PredictionHandler, GetCommentHandler, AddCommentHandler)
