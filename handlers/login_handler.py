from google.appengine.ext import ndb
from base_handler import BlogHandler
from models import *
from utility import *

class LoginHandler(BlogHandler):
    def get(self):
        print "show login"
        user_id = self.check_for_valid_cookie()
        if user_id:
            user = User.get_by_id(int(user_id))
            if user:
                already_logged_in = "You're already logged into the system..."
                self.render("login.html", user=user, already_logged_in=already_logged_in)
            else:
                self.render("login.html")
        else:
            self.render("login.html")

    def post(self):
        has_error = False
        u_name = self.request.get('username')
        password = self.request.get('password')
        remember = self.request.get('remember')

        if u_name and password:
            print "username and password present"
            user = User.query(ndb.AND \
                             (ndb.OR \
                             (User.user_name == u_name, User.email == u_name), \
                             User.password == hash_str(password))).get()
            if user:
                print "valid id and pass"
                user_random = self.request.cookies.get('random')
                if user_random:
                    print "cookie present"
                    is_valid_cookie = check_secure_val(user_random)
                    if is_valid_cookie:
                        print "cookie valid"
                        self.redirect('/home')
                    else:
                        self.response.headers.add_header('Set-Cookie', 'random=''')
                        cookie_error = "Your session has expired! Please log in again to continue!"
                        self.render('login.html', cookie_error=cookie_error)

                else:
                    if remember == 'on':
                        print "remember"
                        lease = 30*24*3600
                        ends = time.gmtime(time.time() + lease)
                        print "ends: ", ends
                        expires = time.strftime("%a, %m %B %Y %H:%M:%S GMT", ends)
                        print "expires: ", expires
                        #self.response.headers.add_header('Expires', lease)
                        self.response.headers.add_header(
                            'Set-Cookie', 'random=%s ; Expires = %s' % \
                            (make_secure_val(str(user.key.id())), expires))
                    else:
                        self.response.headers.add_header(
                            'Set-Cookie', 'random=%s ; Expires = %s' % \
                        (make_secure_val(str(user.key.id())), str(7*24*3600)))
                        print "no remember"
                    self.redirect('/home')
            else:
                error = 'Username and Password do not match!'
                self.render("login.html", username=u_name, error=error)
        else:
            error = "Both username and password are needed! \
                You did not enter either one or both fields!"
            self.render("login.html", username=u_name, error=error)
