import sys

from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy import create_engine

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'  # representation of table inside database

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))


class Category(Base):
    __tablename__ = 'category'  # representation of table inside database

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Return data in serializeable format"""
        return {
            'category-id': self.id,
            'category-name': self.name,
        }


class Item(Base):
    __tablename__ = 'item'  # representation of table inside database

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    description = Column(String(250), nullable=False)
    url = Column(Text, nullable=True, unique=True)
    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship(
        Category, backref=backref("items", cascade="all, delete-orphan"))
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Return data in serializeable format"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category-id': self.category_id,
            'image-name': self.url,
        }


engine = create_engine('postgresql:///itemcatalog')

# add class as new table in database
Base.metadata.create_all(engine)
