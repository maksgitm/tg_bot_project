import sqlalchemy
from sqlalchemy_serializer import SerializerMixin
from data.db_session import SqlAlchemyBase


class Info(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'ads'
    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer)
    ad_data = sqlalchemy.Column(sqlalchemy.BLOB)
    type = sqlalchemy.Column(sqlalchemy.String)
    format = sqlalchemy.Column(sqlalchemy.String)
    description = sqlalchemy.Column(sqlalchemy.String)
    status = sqlalchemy.Column(sqlalchemy.String, nullable=True, default='В работе')
