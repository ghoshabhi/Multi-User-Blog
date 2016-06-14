from google.appengine.ext import ndb
from google.appengine.ext import blobstore

class User(ndb.Model):
    fullname = ndb.StringProperty(required=True)
    user_name = ndb.StringProperty(required=True)
    about = ndb.StringProperty()
    email = ndb.StringProperty(required=True)
    password = ndb.TextProperty(indexed=True,required=True)
    location = ndb.StringProperty()


class Post(ndb.Model):
    title = ndb.StringProperty(required=True)
    content = ndb.TextProperty(required=True)
    created = ndb.DateTimeProperty(auto_now_add = True)
    last_modified = ndb.DateTimeProperty(auto_now = True)
    user = ndb.KeyProperty(kind=User)


class UserPhoto(ndb.Model):
    user = ndb.KeyProperty(kind=User)
    photo_blob_key = ndb.BlobKeyProperty()


class Likes(ndb.Model):
    post = ndb.KeyProperty(kind=Post)
    user_id = ndb.PickleProperty()
    like_count = ndb.IntegerProperty(default=0)


class Comments(ndb.Model):
    user = ndb.KeyProperty(kind=User)
    post = ndb.KeyProperty(kind=Post)
    comment = ndb.StringProperty(required=True)
    comment_date = ndb.DateTimeProperty(auto_now_add=True)