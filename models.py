from google.appengine.ext import ndb

class Post(ndb.Model):
    subject = ndb.StringProperty(required=True)
    content = ndb.TextProperty(required=True)
    created = ndb.DateTimeProperty(auto_now_add = True)
    last_modified = ndb.DateTimeProperty(auto_now = True)
    user = ndb.KeyProperty(required=True)

class User(ndb.Model):
    fullname = ndb.StringProperty(required=True)
    user_name = ndb.StringProperty(required=True)
    email = ndb.StringProperty(required=True)
    password = ndb.TextProperty(indexed=True,required=True)
    photo = ndb.StringProperty()
    location = ndb.StringProperty()