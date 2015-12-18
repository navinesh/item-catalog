#Item catalog
Python web application that provides a list of items within a variety of categories.

It integrates Google and Facebook third party user registration and authentication.
Authenticated users have the ability to post, edit, and delete their own categories and items.

Instant items search function using jQuery AJAX and JSON

##Required Libraries and Dependencies
* Vagrant and VirtualBox - For installing the Vagrant VM, including all the packages https://www.udacity.com/wiki/ud197/install-vagrant

* Python 2.7
* Flask microframework 0.9
* PostgreSQL 9.3.10
* SQLAlchemy

**What's included**

Within the download you will find the following directory and files.

```
catalog/
├──application.py
├──database_setup.py
├──db.sql
├──data.py
├──client_secrets.json
├──fb_client_secrets.json
├──static/
├──templates/
├──uploads/
```

##How to Run the Project
1. Fork https://github.com/navinesh/Item-catalog
2. Clone the newly forked repository to your computer
3. Using the terminal, change directory to **vagrant** (cd vagrant), then type `vagrant up` to launch your virtual machine
4. Once it is up and running, type `vagrant ssh` to log into it
5. Change directory to **vagrant/catalog** (cd /vagrant/catalog)
6. Run the command `psql -f db.sql` to create the database
7. Run the command `python data.py` to create dummy data
8. Run the command `python application.py` to run the application

##Extra Credit Description
- JSON and XML APIs
- Logged-in users can upload/change item image
- Item images are read from database and displayed on the page
- Prevents cross-site request forgery on new, edit and delete category and item functions
- Prevents duplicate categories

##Creator
Navinesh Chand
* https://twitter.com/navinesh
* https://github.com/navinesh
