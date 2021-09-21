from .prediction import PredictionHandler
from .getcomments import GetCommentHandler
from .addcomments import AddCommentHandler
from .topcomments import GetTopComment
from .addfeedback import AddFeedbackHandler
from .getfeedback import GetFeedBackHandler

# HANDLERS = (CheckToken, CreateToken, UploadFile, PredictionHandler)


HANDLERS = (
    PredictionHandler,
    GetCommentHandler,
    AddCommentHandler,
    GetTopComment,
    AddFeedbackHandler,
    GetFeedBackHandler
)
