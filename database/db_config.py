from peewee import *

db = SqliteDatabase("events.db")
cursor = db.cursor()


class Database:
    connection = db
    cursor = cursor
