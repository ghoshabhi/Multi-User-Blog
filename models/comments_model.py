from google.appengine.ext import ndb
from google.appengine.ext import blobstore

class Comments(ndb.Model):
    user = ndb.KeyProperty(kind='User')
    post = ndb.KeyProperty(kind='Post')
    comment = ndb.StringProperty(required=True)
    comment_date = ndb.DateTimeProperty(auto_now_add=True)
