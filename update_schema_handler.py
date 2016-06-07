import webapp2
from google.appengine.ext import deferred

class UpdateHandler(webapp2.RequestHandler):
    def get(self):
        deferred.defer()
        self.response.out.write('Schema migration successfully initiated.')

app = webapp2.WSGIApplication([('/update_schema', UpdateHandler)])