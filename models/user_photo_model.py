from google.appengine.ext import ndb
from google.appengine.ext import blobstore

class UserPhoto(ndb.Model):
    user = ndb.KeyProperty(kind='User')
    photo_blob_key = ndb.BlobKeyProperty()
