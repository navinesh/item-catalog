import os
from flask import Flask, render_template, redirect, url_for, request, \
    jsonify, send_from_directory, flash
from werkzeug import secure_filename

# Imports for login session
from flask import session as login_session
import random
import string

# Libaries to handle code sent from call-back method
# create flow object from client secret json file which stores client-id,
# client-secret, other o-auth paramaters
from oauth2client.client import flow_from_clientsecrets
# catch error when exchanging authorisation code for access token
from oauth2client.client import FlowExchangeError
import httplib2  # http library
import json  # provides api for converting in memory python objects to json
from flask import make_response  # convert return value from function to object
import requests  # Apache2 HTTP library that send HTTP/1.1 requests

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item


# Declare client-id by referencing client secrets file
CLIENT_ID = json.loads(open('client_secrets.json', 'r').read())[
    'web']['client_id']


# Directory to store images
UPLOAD_FOLDER = 'uploads/'
# Image extensions allowed to be uploaded
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

engine = create_engine('postgresql:///itemcatalog')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    """create a state token to prevent request forgery
    and store it in the session for later verification"""
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)  # render login template


@app.route('/')
@app.route('/categories/')
def showCategories():
    """displays all categories in database"""
    categories = session.query(Category).all()
    items = session.query(Item).all()
    return render_template('categories.html', categories=categories,
                           items=items)


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


@app.route('/<filename>/')
@app.route('/categories/<filename>/')
def uploaded_Image(filename):
    """serve uploaded images for home page"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/categories/<int:category_id>/items/<filename>/')
def uploaded_showImage(filename, category_id):
    """serve uploaded images for category view"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/categories/<int:category_id>/<items_id>/<filename>/')
@app.route('/categories/<int:category_id>/<items_id>/edit/<filename>')
def uploaded_editImage(filename, category_id, items_id):
    """serve uploaded image for edit"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/categories/<int:category_id>/<items_id>/')
def showItem(items_id, category_id):
    """displays details of single item"""
    category = session.query(Category).filter_by(id=category_id).first()
    item = session.query(Item).filter_by(id=items_id).one()
    return render_template('item.html', item=item, category=category)


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


# JSON APIs to view sports catalog
@app.route('/catalog.json/')
def catalogJSON():
    categories = session.query(Category).all()
    items = session.query(Item).all()
    return jsonify(Categories=[c.serialize for c in categories],
                   Items=[i.serialize for i in items])


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
    return jsonify(Item=[items.serialize])


@app.errorhandler(404)
def page_not_found(error):
    """redirect user if a page does not exist"""
    return render_template('error.html'), 404


if __name__ == '__main__':
    app.secret_key = 'super secret key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
