from google.appengine.ext import ndb
from google.appengine.ext import blobstore

class User(ndb.Model):
    fullname = ndb.StringProperty(required=True)
    user_name = ndb.StringProperty(required=True)
    about = ndb.StringProperty()
    email = ndb.StringProperty(required=True)
    password = ndb.TextProperty(indexed=True,required=True)
    location = ndb.StringProperty()
    avatar_url = ndb.StringProperty()
