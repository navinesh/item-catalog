from flask import Flask, render_template, redirect, url_for
app = Flask(__name__)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Categories, Items

engine = create_engine('postgresql:///itemcatalog')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

@app.route('/')
@app.route('/categories')
def showCategories():
    """displays all categories"""
    categories = session.query(Categories).all()
    return render_template('categories.html', categories=categories)

@app.route('/categories/new/', methods=['GET', 'POST'])
def newCategories():
    """add new category to database"""
    if method == 'POST':
        newCategories = Categories(name=request.form['name'])
        session.add(newCategories)
        session.commit()
    return redirect(url_for('showCategories'))    



if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
