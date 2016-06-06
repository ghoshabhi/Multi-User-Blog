import os
import webapp2
import jinja2
import re
import hashlib
import hmac
import json

from models import *
from google.appengine.ext import ndb

template_dir = os.path.join(os.path.dirname(__file__),'templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),
                            autoescape = True)

SECRET = "mysecretkey"
error_list = []

empty_content = '<!DOCTYPE html>\n<html>\n<head>\n</head>\n<body>\n\n</body>\n</html>'
empty_title = "<div>&nbsp;</div>"

def hash_str(s):
    return hmac.new(SECRET,s).hexdigest()

def make_secure_val(s):
    return "%s|%s" % (s,hash_str(s))

def check_secure_val(h):
    val = h.split("|")[0]
    if h == make_secure_val(val):
        return val

USERNAME_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
def valid_username(username):
    return username and USERNAME_RE.match(username)


PASS_RE = re.compile(r"^.{3,20}$")
def valid_password(password):
    return password and PASS_RE.match(password)


EMAIL_RE  = re.compile(r'^[\S]+@[\S]+\.[\S]+$')
def valid_email(email):
    return not email or EMAIL_RE.match(email)


def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params) 


def check_for_valid_cookie(self):
    user_email_cookie = self.request.cookies.get('user_email')
    if user_email_cookie:
        if_valid_cookie = check_secure_val(user_email_cookie)
        if if_valid_cookie:
             return self.request.cookies.get('user_email').split("|")[0]
        else:
            return None
    else:
        return None

def filterKey(key):
    return key.id()
    
jinja_env.filters['filterKey'] = filterKey

class BlogHandler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        return render_str(template, **params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))


class HomeHandler(BlogHandler):
    def get(self,user=None):
        posts = []
        user_email = check_for_valid_cookie(self)
        loggedin_user = User.query(User.email == user_email).get()
        posts = Post.query().order(-Post.created)
        all_users = User.query()
        
        if user_email:
            self.render('home.html',user=loggedin_user,all_users=all_users,posts=posts)
        else:
            self.render('home.html',user=loggedin_user,all_users=all_users,posts=posts)


class LoginHandler(BlogHandler):
    def get(self):
        user_email = check_for_valid_cookie(self)
        user = User.query(User.email == user_email).get()

        if user:
            already_logged_in = "You're already logged into the system..."
            self.render("login.html",already_logged_in=already_logged_in)
        else:
            self.render("login.html")
    def post(self):
        has_error = False
        u_name = self.request.get('username') 
        password = self.request.get('password')
        
        if u_name and password:
            user = User.query(ndb.OR(User.user_name==u_name , User.email==u_name) and User.password== hash_str(password)).get()
            if user:
                if self.request.cookies.get('user_email'):
                    user_email_cookie = self.request.cookies.get('user_email')
                    if_valid_cookie = check_secure_val(user_email_cookie)
                    if if_valid_cookie:
                        self.redirect('/home')
                    else:
                        self.response.headers.add_header('Set-Cookie','user_email=''')
                        cookie_error = "Your session has expired! Please log in again to continue!"
                        self.render('login.html',cookie_error=cookie_error)

                else:
                    self.response.headers.add_header('Set-Cookie','user_email=%s' % make_secure_val(str(user.email)))
                    self.redirect('/home')
            else:
                error = 'Username and Password do not match!'
                self.render("login.html",username=u_name,error=error)
        else:
            error = "Both username and password are needed! \
                You did not enter either one or both fields!"
            self.render("login.html", username=u_name,error=error)


class LogOutHandler(BlogHandler):
    def get(self):
        self.response.headers.add_header('Set-Cookie','user_email=''')
        thank_you_for_visiting = "Thank you for visiting this site.\
            We appreciate your presence!"
        self.render('login.html',thank_you_for_visiting = thank_you_for_visiting)


class RegistrationHandler(BlogHandler):
    def get(self):
        self.render("register.html")
    def post(self):
        has_error = False

        fullname = self.request.get('fullname')
        location = self.request.get('location')
        email = self.request.get('email')
        u_name = self.request.get('username') 
        password = self.request.get('password')
        conf_pass = self.request.get('confirm_password')

        if fullname and email and u_name and password and conf_pass and location:
            if not valid_username(u_name):
                error_list.append('The Username is not valid!\
                    Username should not have any special characters!')
                has_error = True
            if not valid_email(email):
                error_list.append('The Email is not valid!\
                    Email should be of the format : abc@example.com!')
                has_error = True
            if not valid_password(password):
                error_list.append("password should be greater than 3 \
                    characters and less than 20 characters!")
                has_error = True
            elif password != conf_pass:
                error_list.append("Both Passwords should match!")
                has_error = True

            user = User.query(User.email == email).get()
            if user:
                error_list.append("That email address already exists!")
                has_error = True
            
            user = User.query(User.user_name == u_name).get()
            if user:
                error_list.append('Sorry that username is already taken!\
                    You should try another username!')
                has_error = True

            if has_error:
                self.render('register.html',fullname=fullname,
                                            location=location,
                                            email=email,
                                            user_name=u_name,
                                            error_list=error_list)
            else:
                new_user = User(fullname=fullname,
                                location=location,
                                email=email,
                                user_name=u_name,
                                password= hash_str(password))
                new_user_key = new_user.put()
                # message = mail.EmailMessage(
                #                 sender='hello@your-own-blog.appspotmail.com',
                #                 subject="Thank You for Connecting with Us!")

                # message.to = email
                # message.body = """Dear %s:

                #         Your your-own-blog account has been approved.  You can now visit
                #         http://your-own-blog.appspot.com and sign in using your Google Account to
                #         access new features.

                #         Please let us know if you have any questions.

                #         The your-own-blog Team
                #         """ % (fullname)
                # message.send()
                self.response.headers.add_header('Set-Cookie','user_email=%s' % make_secure_val(str(new_user.email)))
                self.render('login.html',new_user=new_user.fullname)
        else:
            error_list.append("You did not fill atleast one of the fields!")
            self.render('register.html', fullname=fullname,
                                        location=location,
                                        email=email,
                                        user_name=u_name,
                                        error_list=error_list)

class NewPostHandler(BlogHandler):
    def get(self):
        user_email = check_for_valid_cookie(self)
        if user_email:
            user = User.query(User.email == user_email).get()
            self.render('newpost.html',user=user)
        else:
            cookie_error = "Your session has expired please login again to continue!"
            self.render('login.html',cookie_error = cookie_error)
    
    def post(self):
        user_email = check_for_valid_cookie(self)
        if user_email:
            content = self.request.get('content')
            title = self.request.get('post-title')
            user = User.query(User.email == user_email).get()

            if title!='Click here to give a Title!' and \
             content!='<p>Start writing here...</p>':
                new_post = Post(
                    title = title,
                    content = content,
                    user = user.key
                    )
                new_post_key = new_post.put()
                self.redirect('/blog/%s' % str(new_post_key.id()))
            else:
                empty_post = "Both Title and Content needed for the Blog!"
                self.render('newpost.html',user = user,empty_post = empty_post)
        else:
            cookie_error = "Your session has expired please login again to continue!"
            self.render('login.html',cookie_error = cookie_error)

        # Debug method to avoid DB writes!
        # user_email = check_for_valid_cookie(self)
        # if user_email:
        #     content = self.request.get('content')
        #     title = self.request.get('post-title')
        #     user = User.query(User.email == user_email).get()
            
        #     if title!='Click here to give a Title!' and content!='<p>Start writing here...</p>':
        #         self.write('Thank You!<br>' + title + "<br>" + content)
        #     else:
        #         self.write('Empty Content!')
        # else:
        #     cookie_error = "Your session has expired please login again to continue!"
        #     self.render('login.html',cookie_error = cookie_error)

class PostPage(BlogHandler):
    def get(self, post_id):
        user_email = check_for_valid_cookie(self)
        user = User.query(User.email == user_email).get()
        post = Post.get_by_id(int(post_id))

        if user_email:
            if not post:
                self.error(404)
                return

        self.render("blog.html", post = post,user=user)


class AboutUsHandler(BlogHandler):
    def get(self):
        user_email = check_for_valid_cookie(self)
        user = User.query(User.email == user_email).get()

        if user_email:
            self.render('aboutus.html',user=user)
        else:
            self.render('aboutus.html',user=user)

class TestHandler(BlogHandler):
    def get(self):
        posts = []
        user_email = check_for_valid_cookie(self)
        loggedin_user = User.query(User.email == user_email).get()
        all_users = User.query()
        posts = Post.query()
        # for each_user in all_users:
        #     each_post = Post.query(Post.user == each_user.key).fetch()
        #     posts.append(each_post)

        # for post in posts:
        #     return self.write(post)

        # for each_user_from_db in ndb.gql('select * from User'):
        #     for post in ndb.gql('select * from Post where user=:1',each_user_from_db.key):
        #         all_users = each_user_from_db
        #         posts.append(post)

        if user_email:
            self.render('test.html',user = loggedin_user, all_users=all_users,posts=posts)
        else:
            self.render('test.html',user=loggedin_user,all_users=all_users,posts=posts)



app = webapp2.WSGIApplication([
    ('/', HomeHandler),
    ('/home', HomeHandler),
    ('/login', LoginHandler),
    ('/register',RegistrationHandler),
    ('/logout', LogOutHandler),
    ('/aboutus',AboutUsHandler),
    ('/newpost',NewPostHandler),
    ('/blog/([0-9]+)', PostPage),
    ('/test',TestHandler),
    ], debug=True)
