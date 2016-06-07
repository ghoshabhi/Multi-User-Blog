from google.appengine.ext import ndb
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.ext import blobstore

class User(ndb.Model):
    fullname = ndb.StringProperty(required=True)
    user_name = ndb.StringProperty(required=True)
    about = ndb.StringProperty()
    email = ndb.StringProperty(required=True)
    photo = ndb.BlobProperty()
    password = ndb.TextProperty(indexed=True,required=True)
    location = ndb.StringProperty()


class Post(ndb.Model):
    title = ndb.StringProperty(required=True)
    content = ndb.TextProperty(required=True)
    created = ndb.DateTimeProperty(auto_now_add = True)
    last_modified = ndb.DateTimeProperty(auto_now = True)
    user = ndb.KeyProperty(kind=User)

# class UserPhoto(ndb.Model):
#     user = ndb.KeyProperty(kind=User)
#     photo_blob = ndb.BlobProperty()

class Comments(ndb.Model):
    user = ndb.KeyProperty(kind=User)
    post = ndb.KeyProperty(kind=Post)
    comment = ndb.StringProperty()