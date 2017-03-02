from google.appengine.ext import ndb
from google.appengine.ext import blobstore

class Likes(ndb.Model):
    post = ndb.KeyProperty(kind='Post')
    user_id = ndb.IntegerProperty(repeated=True)
    like_count = ndb.IntegerProperty(default=0)
