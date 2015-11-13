from flask import Flask
app = Flask(__name__)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Categories, Items

engine = create_engine('')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

@app.route('/')
def HelloWorld():
    return "Hello World!"


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
