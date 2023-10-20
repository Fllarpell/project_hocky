from peewee import *
from . import db_config
from datetime import date


class BaseModel(Model):
    class Meta:
        database = db_config.db


# Admin model
class Event(BaseModel):
    id = AutoField()
    name = Field(column_name="name")
    group = Field(column_name="groupID")
    org = Field(column_name="orgID")
    date = DateField(column_name="date")
    fund = Field(column_name="fund")

    class Meta:
        table_name = "Events"
        primary_key = False

    @classmethod
    def validate_date(cls, event_date):
        # if event_date < date.today():
        pass

    @classmethod
    def save_event(cls, orgID, group, name, event_date, fund=0):
        # # Validate the date
        # cls.validate_date(event_date)

        # # Try to retrieve an existing event with the same org and group
        # existing_event = cls.get_or_none(org=orgID, group=group, name=name)

        # if existing_event:
        #     # Update the existing event if it exists
        #     existing_event.name = name
        #     existing_event.date = event_date
        #     existing_event.fund = fund
        #     existing_event.save()
        # else:
        #     # Create a new event if it doesn't exist
        cls.create(org=orgID, group=group, name=name, date=event_date, fund=fund).save()


def initialize_db():
    db_config.db.create_tables([Event], safe=True)
    db_config.db.close()


initialize_db()
