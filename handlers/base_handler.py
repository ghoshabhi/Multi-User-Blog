import webapp2
import os
import jinja2
from utility import check_secure_val, filterKey, showCount
from models import User

template_dir = os.path.join(os.path.dirname(__file__), '../views')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),
                              autoescape=True)

jinja_env.filters['filterKey'] = filterKey
jinja_env.filters['showCount'] = showCount

def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)

class BlogHandler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        return render_str(template, **params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

    def get_user_from_cookie(self):
        random = self.check_for_valid_cookie()
        print "random: ", random
        if random:
            user = User.get_by_id(int(random))
            print "user: ", user
            return user
        else:
            print "None"
            return None
    def check_for_valid_cookie(self):
        random = self.request.cookies.get('random')
        if random:
            is_valid_cookie = check_secure_val(random)
            if is_valid_cookie:
                return self.request.cookies.get('random').split("|")[0]
        return None
