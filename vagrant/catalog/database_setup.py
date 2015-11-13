import sys

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

class Categories(Base):
    __tablename__ = 'categories'


class Items(Base):
    __tablename__ = 'items'
    

engine = create_engine('')

Base.metadata.create_all(engine)
