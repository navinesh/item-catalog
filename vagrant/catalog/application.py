import os
from flask import Flask, render_template, redirect, url_for, request, \
    jsonify, send_from_directory
from werkzeug import secure_filename

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item

# directory to store images
UPLOAD_FOLDER = 'uploads/'
# image extensions allowed to be uploaded
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

engine = create_engine('postgresql:///itemcatalog')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


@app.route('/')
@app.route('/categories/')
def showCategories():
    """displays all categories in database"""
    categories = session.query(Category).all()
    items = session.query(Item).all()
    return render_template('categories.html', categories=categories, items=items)


@app.route('/home/')
def shows():
    """displays all categories in database"""
    categories = session.query(Category).all()
    items = session.query(Item).all()
    return render_template('home.html', categories=categories, items=items)


@app.route('/categories/new/', methods=['GET', 'POST'])
def newCategory():
    """add new category to the database"""
    if request.method == 'POST':
        newCategory = Category(name=request.form['name'])
        session.add(newCategory)
        session.commit()
        return redirect(url_for('showCategories'))
    else:
        return render_template('newcategory.html')


@app.route('/categories/<int:category_id>/edit/', methods=['GET', 'POST'])
def editCategory(category_id):
    """edit category"""
    editCategory = session.query(Category).filter_by(id=category_id).one()
    if request.method == 'POST':
        if request.form['name']:
            editCategory.name = request.form['name']
            session.add(editCategory)
            session.commit()
            return redirect(url_for('showCategories'))
    else:
        return render_template('editcategory.html', i=editCategory)


@app.route('/categories/<int:category_id>/delete/', methods=['GET', 'POST'])
def deleteCategory(category_id):
    """delete category"""
    deleteCategory = session.query(Category).filter_by(id=category_id).one()
    if request.method == 'POST':
        session.delete(deleteCategory)
        session.commit()
        return redirect(url_for('showCategories'))
    else:
        return render_template('deletecategory.html', i=deleteCategory)


@app.route('/categories/<int:category_id>/<filename>')
@app.route('/categories/<int:category_id>/items/<filename>')
def uploaded_file(filename, category_id):
    """serve uploaded images"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/categories/<int:category_id>/<items_id>/edit/<filename>')
def uploaded_image(filename, category_id, items_id):
    """serve uploaded image for edit"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/categories/<int:category_id>/')
@app.route('/categories/<int:category_id>/items/')
def showItems(category_id):
    """displays all items in each category"""
    category = session.query(Category).filter_by(id=category_id).first()
    items = session.query(Item).filter_by(category_id=category_id)
    return render_template('items.html', category=category, items=items)


def allowed_file(filename):
    """check if an image extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/categories/<int:category_id>/items/new/', methods=['GET', 'POST'])
def newItem(category_id):
    """add new item for a particular category in the database"""
    category = session.query(Category).filter_by(id=category_id).first()
    if request.method == 'POST':
        file = request.files['file']  # check if an image was posted
        if file and allowed_file(file.filename):  # check extension
            filename = secure_filename(file.filename)  # return secure version
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        else:
            filename = None
        newItem = Item(name=request.form['name'], category_id=category_id,
                       description=request.form['description'], url=filename)
        session.add(newItem)
        session.commit()
        return redirect(url_for('showItems', category_id=category_id))
    else:
        return render_template('newitem.html', category_id=category_id,
                               category_name=category.name)


@app.route('/categories/<int:category_id>/<items_id>/edit/',
           methods=['GET', 'POST'])
def editItem(category_id, items_id):
    """edit item of a particular category"""
    categories = session.query(Category).all()
    editItem = session.query(Item).filter_by(id=items_id).one()
    if request.method == 'POST':
        if request.form['name']:
            editItem.name = request.form['name']
        if request.form['description']:
            editItem.description = request.form['description']
        file = request.files['file']  # check if an image was posted
        if file and allowed_file(file.filename):  # check extension
            filename = secure_filename(file.filename)  # return secure version
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            editItem.url = filename
            session.add(editItem)
            session.commit()
            return redirect(url_for('showItems', category_id=category_id))
    else:
        return render_template('edititem.html', category_id=category_id,
                               i=editItem, c=categories)


@app.route('/categories/<int:category_id>/<items_id>/delete/',
           methods=['GET', 'POST'])
def deleteItem(category_id, items_id):
    """delete item of a particular category"""
    deleteItem = session.query(Item).filter_by(id=items_id).one()
    if request.method == 'POST':
        session.delete(deleteItem)
        session.commit()
        return redirect(url_for('showItems', category_id=category_id))
    else:
        return render_template('deleteitem.html', category_id=category_id,
                               i=deleteItem)


@app.route('/catalog.json/')
def catalogJSON():
    categories = session.query(Category).all()
    items = session.query(Items).all()
    return jsonify(Categories=[c.serialize for c in categories], Items=[i.serialize for i in items])


@app.route('/categories/json/')
def categoriesJSON():
    categories = session.query(Category).all()
    return jsonify(Categories=[c.serialize for c in categories])


@app.route('/categories/<int:category_id>/items/json/')
def categoryItemJSON(category_id):
    items = session.query(Item).filter_by(category_id=category_id).all()
    return jsonify(Items=[i.serialize for i in items])


@app.route('/categories/<int:category_id>/items/<int:items_id>/json/')
def categoryItemsJSON(category_id, items_id):
    items = session.query(Item).filter_by(id=items_id).one()
    return jsonify(Items=[items.serialize])


@app.errorhandler(404)
def page_not_found(error):
    """redirect user if a page does not exist"""
    return render_template('error.html'), 404


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
