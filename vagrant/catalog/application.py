from flask import Flask, render_template, redirect, url_for, request
app = Flask(__name__)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Categories, Items

engine = create_engine('postgresql:///itemcatalog')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

@app.route('/')
@app.route('/categories/')
def showCategories():
    """displays all categories in database"""
    categories = session.query(Categories).all()
    return render_template('categories.html', categories=categories)

@app.route('/categories/new/', methods=['GET', 'POST'])
def newCategories():
    """add new category to database"""
    if request.method == 'POST':
        newCategories = Categories(name=request.form['name'])
        session.add(newCategories)
        session.commit()
        return redirect(url_for('showCategories'))
    else:
        return render_template('newcategories.html')

@app.route('/categories/<int:categories_id>/')
@app.route('/categories/<int:categories_id>/items/')
def showItems(categories_id):
    """displays all items in in each category"""
    categories = session.query(Categories).filter_by(id=categories_id).first()
    items = session.query(Items).filter_by(categories_id=categories_id)
    return render_template('items.html', categories=categories, items=items)

@app.route('/categories/<int:categories_id>/items/new/', methods=['GET', 'POST'])
def newItem(categories_id):
    """add new item for a particular category in the database"""
    if request.method == 'POST':
        newItem = Items(name=request.form['name'], categories_id=categories_id, description=request.form['description'])
        session.add(newItem)
        session.commit()
        return redirect(url_for('showItems', categories_id=categories_id))
    else:
        return render_template('newitem.html', categories_id=categories_id)


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
