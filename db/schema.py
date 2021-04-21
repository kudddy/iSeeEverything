from enum import Enum, unique

from sqlalchemy import (
    Column, Date, Enum as PgEnum, ForeignKey, ForeignKeyConstraint, Integer,
    MetaData, String, Table
)

from sqlalchemy.types import UserDefinedType

# SQLAlchemy рекомендует использовать единый формат для генерации названий для
# индексов и внешних ключей.
# https://docs.sqlalchemy.org/en/13/core/constraints.html#configuring-constraint-naming-conventions
convention = {
    'all_column_names': lambda constraint, table: '_'.join([
        column.name for column in constraint.columns.values()
    ]),
    'ix': 'ix__%(table_name)s__%(all_column_names)s',
    'uq': 'uq__%(table_name)s__%(all_column_names)s',
    'ck': 'ck__%(table_name)s__%(constraint_name)s',
    'fk': 'fk__%(table_name)s__%(all_column_names)s__%(referred_table_name)s',
    'pk': 'pk__%(table_name)s'
}

metadata = MetaData(naming_convention=convention)


# добавлена поддерка типа CUBE
class CUBE(UserDefinedType):
    def get_col_spec(self, **kw):
        return "CUBE"


comments = Table(
    'comments',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('file', String),
    Column('comment', String),
    Column('date', Date)
)



# all_tokens = Table(
#     'tokens',
#     metadata,
#     Column('token', String),
#     Column('upload_date', Date),
#     Column('model_uid', String)
# )

# done_encoders = Table(
#     'done_encoders',
#     metadata,
#     Column('token', String),
#     Column('encoders_uid', String)
#
# )

# cursor.execute("create extension if not exists cube;")
# cursor.execute("drop table if exists vectors")
# cursor.execute("create table vectors (id serial, file varchar, date timestamp, vec_low cube, vec_high cube);")
# cursor.execute("create index vectors_vec_idx on vectors (vec_low, vec_high);")

# encoders = Table(
#     'encoders',
#     metadata,
#     Column('token', )
# )
