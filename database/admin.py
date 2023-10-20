from peewee import *
from . import db_config


class BaseModel(Model):
    class Meta:
        database = db_config.db


# Admin model
class Admin(BaseModel):
    tg_id = Field(column_name="tgID")
    group_ID = Field(column_name="groupID")

    class Meta:
        table_name = "admins"
        primary_key = False

    @classmethod
    def get_channels(cls, tg_id):
        result = (
            cls.select(cls.tg_id, cls.group_ID)
            .distinct()
            .where(cls.tg_id == tg_id)
            .tuples()
        )
        return result


def initialize_db():
    db_config.db.create_tables([Admin], safe=True)
    db_config.db.close()


initialize_db()
