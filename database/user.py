from peewee import *
from . import db_config


class BaseModel(Model):
    class Meta:
        database = db_config.db


# Admin model
class User(BaseModel):
    tg_id = Field(column_name="tgID")
    firstname = Field(column_name="firstname")
    lastname = Field(column_name="lastname")
    username = Field(column_name="username")

    class Meta:
        table_name = "parents"
        primary_key = False


class UserInGroups(BaseModel):
    tg_id = Field(column_name="tgID")
    group_id = Field(column_name="groupID")

    class Meta:
        table_name = "userIngroups"
        primary_key = False


def initialize_db():
    db_config.db.create_tables([User, UserInGroups], safe=True)
    db_config.db.close()


initialize_db()
