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
from database_setup import Base, Category, Item, User


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


@app.route('/login')
def showLogin():
    """Create anti-forgery state token
    and store it in the session for later verification"""
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # render login template
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gConnect():
    """Google login
    Handle calls sent back by Google sign-in call-back method"""
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state paramater'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    code = request.data  # obtain authorization code

    try:
        # upgrade authorisation code into credentials object
        # which will contain access token for server
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(json.dumps(
            'Failed to upgrade authorisation code'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # check if access token is valid
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])

    # if there was error in access token info then abort
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'

    # verify that access token is used for the intended user
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID does not match user ID"), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # verify that the access token is valid for this app
    if result['issued_to'] != CLIENT_ID:
        response = make_response(json.dumps(
            "Token's client ID does not match app's"), 401)
        print "Token's client ID does not match app's"
        response.headers['Content-Type'] = 'application/json'
        return response

    # check if user is already logged in
    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps
                                 ('Current user is already connected'),
                                 200)
        response.headers['Content-Type'] = 'application/json'

    # store access taken in session for later use
    login_session['provider'] = 'google'
    login_session['credentials'] = credentials
    login_session['gplus_id'] = gplus_id
    response = make_response(json.dumps('Successfully connected user', 200))

    # get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)
    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # check if a user exists in the database, if it doesn't then create it
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px; \
    border-radius: 150px;-webkit-border-radius: 150px; \
    -moz-border-radius: 150px;"> '
    flash("You are now logged in as %s" % login_session['username'])
    print "done!"
    return output


@app.route('/gdisconnect')
def gDisconnect():
    """Log out user, revoke current users' token and
    reset their login_session"""
    # only disconnect a connected user
    credentials = login_session.get('credentials')
    if credentials is None:
        response = make_response(json.dumps("Current user not connected"),
                                 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # execute HTTP GET request to revoke current token
    access_token = credentials.access_token
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s'\
        % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] != '200':
        # if token was invalid
        response = make_response(json.dumps(
            'Failed to revoke token for given user', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/fbconnect', methods=['POST'])
def fbConnect():
    """Facebook login"""
    # verify value of state to prevent cross-site request forgery
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state paramater.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data

    # exchange short-lived token for a long-lived token
    app_id = json.loads(open('fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(open('fb_client_secrets.json', 'r').read())[
        'web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (
        app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    # use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v2.5/me"
    # strip expire tag from access token
    token = result.split("&")[0]

    url = 'https://graph.facebook.com/v2.5/me?%s&fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # token must be stored in the login_session in order to properly logout
    # strip out the information before the equals sign in token
    stored_token = token.split("=")[1]
    login_session['access_token'] = stored_token

    # get user picture
    url = 'https://graph.facebook.com/v2.5/me/picture?%s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)
    login_session['picture'] = data["data"]["url"]

    # check if a user exists in the database, if it doesn't then create it
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px; \
    border-radius: 150px;-webkit-border-radius: 150px; \
    -moz-border-radius: 150px;"> '
    flash("You are now logged in as %s" % login_session['username'])
    print "done!"
    return output


@app.route('/fbdisconnect')
def fbDisconnect():
    """Facebook logout"""
    facebook_id = login_session['facebook_id']
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (
        facebook_id, access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "You have been logged out."


@app.route('/logout')
def logout():
    """Logout user"""
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gDisconnect()
            del login_session['credentials']
            del login_session['gplus_id']
        if login_session['provider'] == 'facebook':
            fbDisconnect()
            del login_session['facebook_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have been successfully logged out.")
        return redirect(url_for('showCategories'))
    else:
        flash("No user logged in.")
        return redirect(url_for('showCategories'))


def createUser(login_session):
    """Get logged-in user info to create new user in database"""
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    """Return user object associated with user ID"""
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    """Return ID number of a user if email address belongs to
    a user in the database. Return none if it does not exist"""
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        None


@app.route('/')
@app.route('/categories/')
def showCategories():
    """Display all categories and its items"""
    categories = session.query(Category).all()
    items = session.query(Item).all()
    if 'username' not in login_session:
        return render_template('public-categories.html',
                               categories=categories,
                               items=items)
    else:
        return render_template('categories.html',
                               categories=categories,
                               items=items)


@app.route('/categories/new/', methods=['GET', 'POST'])
def newCategory():
    """Add new category to the database"""
    # check if user is logged in
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newCategory = Category(
            name=request.form['name'], user_id=login_session['user_id'])
        session.add(newCategory)
        session.commit()
        flash('New category %s successfully created' % (newCategory.name))
        return redirect(url_for('showCategories'))
    else:
        return render_template('newcategory.html')


@app.route('/categories/<int:category_id>/edit/', methods=['GET', 'POST'])
def editCategory(category_id):
    """Edit category"""
    # check if user is logged in
    if 'username' not in login_session:
        return redirect('/login')
    editCategory = session.query(Category).filter_by(id=category_id).one()
    creator = getUserInfo(editCategory.user_id)  # get creator info
    if editCategory.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert\
        ('You are not authorised to edit this item!');}\
        </script><body onload='myFunction()'' >"
    if request.method == 'POST':
        if request.form['name']:
            editCategory.name = request.form['name']
        session.add(editCategory)
        session.commit()
        flash('Category %s successfully edited' % (editCategory.name))
        return redirect(url_for('showCategories'))
    else:
        return render_template('editcategory.html', i=editCategory,
                               creator=creator)


@app.route('/categories/<int:category_id>/delete/', methods=['GET', 'POST'])
def deleteCategory(category_id):
    """Delete category"""
    # check if user is logged in
    if 'username' not in login_session:
        return redirect('/login')
    deleteCategory = session.query(Category).filter_by(id=category_id).one()
    creator = getUserInfo(deleteCategory.user_id)  # get creator info
    if deleteCategory.user_id != login_session['user_id']:
        return "< script > function myFunction() {alert('You are not \
                authorised to edit this item!');}</script> \
                <body onload='myFunction()'' >"
    if request.method == 'POST':
        session.delete(deleteCategory)
        session.commit()
        flash('Categiry %s successfully deleted' % (deleteCategory.name))
        return redirect(url_for('showCategories'))
    else:
        return render_template('deletecategory.html', i=deleteCategory,
                               creator=creator)


@app.route('/<filename>/')
@app.route('/categories/<filename>/')
def uploaded_Image(filename):
    """Serve uploaded images for home page"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/categories/<int:category_id>/items/<filename>/')
def uploaded_showImage(filename, category_id):
    """Serve uploaded images for category view"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/categories/<int:category_id>/<items_id>/<filename>/')
@app.route('/categories/<int:category_id>/<items_id>/edit/<filename>')
def uploaded_editImage(filename, category_id, items_id):
    """Serve uploaded image for edit"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/categories/<int:category_id>/<items_id>/')
def showItem(items_id, category_id):
    """Display details of single item"""
    category = session.query(Category).filter_by(id=category_id).first()
    item = session.query(Item).filter_by(id=items_id).one()
    creator = getUserInfo(category.user_id)  # get creator info
    if 'username' not in login_session or \
            creator.id != login_session['user_id']:
        return render_template('public-item.html', category=category,
                               item=item, creator=creator)
    else:
        return render_template('item.html', category=category,
                               item=item, creator=creator)


@app.route('/categories/<int:category_id>/')
@app.route('/categories/<int:category_id>/items/')
def showItems(category_id):
    """Display all item in each category

    If a user is not logged-in or logged-in user is not the creator of the
    item then render public template otherwise logged-in user is the creator
    of the item so we render template with edit/delete item option
    """
    category = session.query(Category).filter_by(id=category_id).first()
    items = session.query(Item).filter_by(category_id=category_id)
    creator = getUserInfo(category.user_id)  # get creator info
    if 'username' not in login_session or \
            creator.id != login_session['user_id']:
        return render_template('public-items.html', category=category,
                               items=items, creator=creator)
    else:
        return render_template('items.html', category=category, items=items,
                               creator=creator)


def allowed_file(filename):
    """Check if an image extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/categories/<int:category_id>/items/new/', methods=['GET', 'POST'])
def newItem(category_id):
    """Create a new item for a particular category"""
    # check if user is logged in
    if 'username' not in login_session:
        return redirect('/login')
    category = session.query(Category).filter_by(id=category_id).first()
    creator = getUserInfo(category.user_id)  # get creator info
    if login_session['user_id'] != category.user_id:
        return "<script>function myFunction(){alert \
        ('You are not authorised to create new item for this category!');} \
        </script><body onload='myFunction()'' >"
    if request.method == 'POST':
        file = request.files['file']  # check if an image was posted
        if file and allowed_file(file.filename):  # check extension
            filename = secure_filename(file.filename)  # return secure version
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        else:
            filename = None
        newItem = Item(name=request.form['name'],
                       description=request.form['description'],
                       url=filename,
                       category_id=category_id,
                       user_id=login_session['user_id'])
        session.add(newItem)
        session.commit()
        flash('Item %s successfully created' % (newItem.name))
        return redirect(url_for('showItems', category_id=category_id))
    else:
        return render_template('newitem.html', category_id=category_id,
                               category_name=category.name, creator=creator)


@app.route('/categories/<int:category_id>/<items_id>/edit/',
           methods=['GET', 'POST'])
def editItem(category_id, items_id):
    """Edit an item of a particular category"""
    # check if user is logged in
    if 'username' not in login_session:
        return redirect('/login')
    categories = session.query(Category).all()
    category = session.query(Category).filter_by(id=category_id).first()
    creator = getUserInfo(category.user_id)  # get creator info
    editItem = session.query(Item).filter_by(id=items_id).one()
    if login_session['user_id'] != category.user_id:
        return "<script>function myFunction() {alert\
        ('You are not authorised to edit this item!');}\
        </script><body onload='myFunction()'' >"
    if request.method == 'POST':
        if request.form['name']:
            editItem.name = request.form['name']
        if request.form['description']:
            editItem.description = request.form['description']
        if request.form['categoryID']:
            editItem.category_id = request.form['categoryID']
        file = request.files['file']  # check if an image was posted
        if file and allowed_file(file.filename):  # check extension
            filename = secure_filename(file.filename)  # return secure version
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            editItem.url = filename
        session.add(editItem)
        session.commit()
        flash('Item %s successfully edited' % (editItem.name))
        return redirect(url_for('showItems', category_id=category_id))
    else:
        return render_template('edititem.html', category=category,
                               i=editItem, categories=categories,
                               creator=creator)


@app.route('/categories/<int:category_id>/<items_id>/delete/',
           methods=['GET', 'POST'])
def deleteItem(category_id, items_id):
    """Delete an item of a particular category"""
    # check if user is logged in
    if 'username' not in login_session:
        return redirect('/login')
    category = session.query(Category).filter_by(id=category_id).first()
    creator = getUserInfo(category.user_id)  # get creator info
    deleteItem = session.query(Item).filter_by(id=items_id).one()
    if login_session['user_id'] != category.user_id:
        return "<script>function myFunction() {alert\
        ('You are not authorised to delete this item!');}\
        </script><body onload='myFunction()'' >"
    if request.method == 'POST':
        session.delete(deleteItem)
        session.commit()
        flash('Item %s successfully deleted' % (deleteItem.name))
        return redirect(url_for('showItems', category_id=category_id))
    else:
        return render_template('deleteitem.html', category_id=category_id,
                               i=deleteItem, creator=creator)


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
