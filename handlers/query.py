from sqlalchemy import and_, func, select

from db.schema import comments

# CHECK_TOKEN = select([all_tokens.c.token])
#
# GET_MODEL = select([all_tokens.c.model_uid])
#
# GET_ENCODER_UID = select([done_encoders.c.encoders_uid])


COMMENTS_TABLE = select([comments])
