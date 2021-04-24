from .prediction import PredictionHandler
from .getcomments import GetCommentHandler
from .addcomments import AddCommentHandler
from .topcomments import GetTopComment

# HANDLERS = (CheckToken, CreateToken, UploadFile, PredictionHandler)


HANDLERS = (PredictionHandler, GetCommentHandler, AddCommentHandler, GetTopComment)
