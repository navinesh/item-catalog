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
def newCategory():
    """add new category to database"""
    if request.method == 'POST':
        newCategory = Categories(name=request.form['name'])
        session.add(newCategory)
        session.commit()
        return redirect(url_for('showCategories'))
    else:
        return render_template('newcategory.html')

@app.route('/categories/<int:category_id>/')
@app.route('/categories/<int:category_id>/items/')
def showItems(category_id):
    """displays all items in in each category"""
    category = session.query(Categories).filter_by(id=category_id).first()
    items = session.query(Items).filter_by(category_id=category_id)
    return render_template('items.html', category=category, items=items)

@app.route('/categories/<int:category_id>/items/new/', methods=['GET', 'POST'])
def newItem(category_id):
    """add new item for a particular category in the database"""
    category = session.query(Categories).filter_by(id=category_id).first()
    if request.method == 'POST':
        newItem = Items(name=request.form['name'], category_id=category_id, description=request.form['description'])
        session.add(newItem)
        session.commit()
        return redirect(url_for('showItems', category_id=category_id))
    else:
        return render_template('newitem.html', category_id=category_id, category_name=category.name)


@app.route('/categories/<int:category_id>/<items_id>/edit', methods=['GET', 'POST'])
def editItem(category_id, items_id):
    """Edit item of a particular category"""
    categories = session.query(Categories).all()
    editItem = session.query(Items).filter_by(id=items_id).one()
    if request.method == 'POST':
        if request.form['name']:
            editItem.name = request.form['name']
        if request.form['description']:
            editItem.description = request.form['description']
            session.add(editItem)
            session.commit()
            return redirect(url_for('showItems', category_id=category_id))
    else:
        return render_template('edititem.html', category_id=category_id, i=editItem, c=categories)


@app.route('/categories/<int:category_id>/<items_id>/edit', methods=['GET', 'POST'])
def deleteItem(category_id, items_id):
    """Delete item"""
    deleteItem = session.query(Items).filter_by(id=items_id).one()
    if request.method == 'POST':
        session.delete(deleteItem)
        session.commit()
        return redirect(url_for('showItems', category_id=category_id))
    else:
        return render_template('deleteItem.html')

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
