from google.appengine.ext import ndb
from google.appengine.ext import blobstore

class Post(ndb.Model):
    title = ndb.StringProperty(required=True)
    content = ndb.TextProperty(required=True)
    created = ndb.DateTimeProperty(auto_now_add = True)
    last_modified = ndb.DateTimeProperty(auto_now = True)
    is_draft = ndb.BooleanProperty(default=False)
    user = ndb.KeyProperty(kind='User')
