import os
import sys

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

class Categories(Base):
    __tablename__ = 'categories'  # representation of table inside database

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)

    @property
    def serialize(self):
        return {
        'id' : self.id,
        'name' : self.name,
        }

class Items(Base):
    __tablename__ = 'items'  # representation of table inside database

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(250), nullable=False)
    category_id = Column(Integer, ForeignKey('categories.id'))
    categories = relationship(Categories)

    @property
    def serialize(self):
        return {
        'id' : self.id,
        'name' : self.name,
        'description' : self.description,
        }

engine = create_engine('postgresql:///itemcatalog')

# add class as new tables in database
Base.metadata.create_all(engine)
