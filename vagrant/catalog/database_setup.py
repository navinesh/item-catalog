import sys

from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy import create_engine

Base = declarative_base()


class Category(Base):
    __tablename__ = 'category'  # representation of table inside database

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)

    @property
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
        }


class Item(Base):
    __tablename__ = 'item'  # representation of table inside database

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(250), nullable=False)
    url = Column(Text, nullable=True, unique=True)
    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship(
        Category, backref=backref("items", cascade="all, delete-orphan"))

    @property
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category_id': self.category_id,
            'url': self.url,
        }

engine = create_engine('postgresql:///itemcatalog')

# add class as new table in database
Base.metadata.create_all(engine)
