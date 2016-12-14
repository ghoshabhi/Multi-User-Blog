import os
import webapp2
import jinja2
import re
import hashlib
import hmac
import json
import time
import logging

from datetime import datetime
from dateutil import tz
from models import User,Post,UserPhoto,Likes,Comments
from google.appengine.ext import ndb
from google.appengine.api import mail
from google.appengine.api import app_identity
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.ext import blobstore
from google.appengine.api import images
from hash_keys import SECRET

template_dir = os.path.join(os.path.dirname(__file__),'templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),
                            autoescape = True)

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

def filterKey(key):
    return key.id()

def showCount(post_key):
    like_obj = Likes.query(Likes.post == post_key).get()
    if like_obj:
        return like_obj.like_count
    else:
        return "0"

jinja_env.filters['filterKey'] = filterKey
jinja_env.filters['showCount'] = showCount


def check_for_valid_cookie(self):
    random = self.request.cookies.get('random')
    if random:
        is_valid_cookie = check_secure_val(random)
        if is_valid_cookie:
             return self.request.cookies.get('random').split("|")[0]
        else:
            return None
    else:
        return None

class BlogHandler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        return render_str(template, **params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

    def get_user_from_cookie(self):
        random = check_for_valid_cookie(self)
        if random:
            return User.get_by_id(int(random))
        else:
            return None


class HomeHandler(BlogHandler):
    def get(self,user=None):
        posts = []
        cookie_user = self.get_user_from_cookie()
        if cookie_user:
            loggedin_user = cookie_user
        else:
            loggedin_user = None

        posts = Post.query(Post.is_draft == False).order(-Post.created)
        all_users = User.query()
        likes = Likes.query()

        list_dict = []

        for p in posts:
            p_dict = {}
            for u in all_users:
                if p.user == u.key:
                    p_dict['p_id'] = p.key.id()
                    p_dict['p_title'] = p.title
                    p_dict['p_content'] = p.content
                    p_dict['p_created'] = p.created
                    p_dict['a_name'] = u.fullname
                    p_dict['a_key'] = u.key
                    p_dict['a_id'] = u.key.id()
            for l in likes:
                if l.post == p.key:
                    p_dict['like_count'] = l.like_count
            comment_count = Comments.query(Comments.post == p.key).count()
            p_dict['c_count'] = comment_count
            list_dict.append(p_dict)

        return self.render('home.html',user=loggedin_user,
                                       list_dict = list_dict)

class LoginHandler(BlogHandler):
    def get(self):
        user_id = check_for_valid_cookie(self)
        if user_id:
            user = User.get_by_id(int(user_id))
            if user:
                already_logged_in = "You're already logged into the system..."
                self.render("login.html",already_logged_in=already_logged_in)
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
            user = User.query(ndb.AND(ndb.OR(User.user_name==u_name,User.email==u_name),User.password== hash_str(password))).get()
            if user:
                if self.request.cookies.get('random'):
                    user_random = self.request.cookies.get('random')
                    is_valid_cookie = check_secure_val(user_random)
                    if is_valid_cookie:
                        self.redirect('/home')
                    else:
                        self.response.headers.add_header('Set-Cookie','random=''')
                        cookie_error = "Your session has expired! Please log in again to continue!"
                        self.render('login.html',cookie_error=cookie_error)

                else:
                    self.response.headers.add_header('Set-Cookie','random=%s' % make_secure_val(str(user.key.id())))
                    if remember == 'on':
                        lease = 30*24*3600
                        ends = time.gmtime(time.time() + lease)
                        expires = time.strftime("%a, %m %B %Y %H:%M:%S GMT",ends)
                        self.response.headers.add_header('expires', expires)
                        # self.response.headers.add_header('expires', 'Sat, 13 July 2016 12:00:00 GMT')
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
        self.response.headers.add_header('Set-Cookie','random=''')
        thank_you_for_visiting = "Thank you for visiting this site.\
            We appreciate your presence!"
        self.render('login.html',thank_you_for_visiting = thank_you_for_visiting)


class RegistrationHandler(BlogHandler):
    def get(self):
        self.render("register.html")
    def post(self):
        has_error = False
        error_list = []

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

                new_user_photo_obj = UserPhoto(user= new_user_key)
                new_user_photo_obj.put()

                time.sleep(0.2)
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
        cookie_user = self.get_user_from_cookie()
        if cookie_user:
            self.render('newpost.html',user=cookie_user)
        else:
            cookie_error = "Your session has expired please login again to continue!"
            self.render('login.html',cookie_error = cookie_error)

    def post(self):
        cookie_user = self.get_user_from_cookie()
        if cookie_user:
            content = self.request.get('content')
            title = self.request.get('post-title')
            is_draft = self.request.get('draft')

            if is_draft == 'on':
                is_draft = True
            else:
                is_draft =  False

            if title!='Click here to give a Title!' and \
             content!='<p>Start writing here...</p>':
                new_post = Post(
                    title = title,
                    content = content,
                    user = cookie_user.key,
                    is_draft = is_draft
                    )
                new_post_key = new_post.put()
                time.sleep(0.3)
                like_obj = Likes(post=new_post_key,like_count=0)
                like_key = like_obj.put()
                time.sleep(0.1)

                if is_draft:
                    self.redirect('/user/%s/drafts' % str(cookie_user.key.id()))
                else:
                    self.redirect('/blog/%s' % str(new_post_key.id()))
            else:
                empty_post = "Both Title and Content needed for the Blog!"
                self.render('newpost.html',user = cookie_user,
                    title=title, content=content,empty_post = empty_post)
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


class EditBlogHandler(BlogHandler):
    def get(self,post_id):
        # user_id = check_for_valid_cookie(self)
        # cookie_user = User.get_by_id(int(user_id))
        cookie_user = self.get_user_from_cookie()
        post = Post.get_by_id(int(post_id))

        if cookie_user:
            if post:
                self.render('editpost.html',user=cookie_user,
                    post=post)
            else:
                #self.error(404)
                self.render("error.html")
                return
        else:
            cookie_error = "You need to log in before you edit the post!"
            self.render('login.html',cookie_error = cookie_error)

    def post(self,post_id):
        # user_id = check_for_valid_cookie(self)
        # cookie_user = User.get_by_id(int(user_id))
        cookie_user = self.get_user_from_cookie()

        if cookie_user:
            post = Post.get_by_id(int(post_id))
            if post:
                postTitle = self.request.get('post-title')
                postContent = self.request.get('content')
                if postTitle and postContent:
                    post.title = postTitle
                    post.content = postContent
                    post.put()
                    time.sleep(0.2)
                    self.redirect('/blog/%s'%post.key.id())
                else:
                    empty_title_content = True
                    self.render('editpost.html',user=cookie_user,
                        post=post,empty_title_content=empty_title_content)
            else:
                self.error(404)
                return
        else:
            cookie_error = "You need to log in before you edit the post!"
            self.render('login.html',cookie_error = cookie_error)


class DeleteBlogHandler(BlogHandler):
    def get(self,post_id):
        # user_id = check_for_valid_cookie(self)
        # cookie_user = User.get_by_id(int(user_id))
        cookie_user = self.get_user_from_cookie()
        post = Post.get_by_id(int(post_id))

        if cookie_user:
            if post:
                self.render('deletepost.html',user=cookie_user,post=post)
            else:
                self.error(404)
                return
        else:
            cookie_error = "You need to log in before you delete the post!"
            self.render('login.html',cookie_error = cookie_error)

    def post(self,post_id):
        # user_id = check_for_valid_cookie(self)
        # cookie_user = User.get_by_id(int(user_id))
        cookie_user = self.get_user_from_cookie()

        if cookie_user:
            post = Post.get_by_id(int(post_id))
            if post:
                post.key.delete()
                time.sleep(0.2)
                self.redirect('/')
            else:
                self.error(404)
                return
        else:
            cookie_error = "You need to log in before you delete the post!"
            self.render('login.html',cookie_error = cookie_error)



class PostPageHandler(BlogHandler):
    def get(self, post_id):
        # user_id = check_for_valid_cookie(self)
        # cookie_user = User.get_by_id(int(user_id))
        cookie_user = self.get_user_from_cookie()

        post = Post.get_by_id(int(post_id))
        if post:
            comments = Comments.query(Comments.post == post.key).order(-Comments.comment_date)
            likes = Likes.query(Likes.post == post.key).get()

            list_dict = []

            comment_count = comments.count()

            if likes:
                no_of_likes = likes.like_count
            else:
                no_of_likes = 0

            for c in comments:
                c_dict = {}
                if c.post == post.key:
                    c_dict['c_id'] = c.key.id()
                    c_dict['c_comment'] = c.comment
                    c_dict['c_date'] = c.comment_date
                    user = User.query(User.key == c.user).get()
                    c_dict['c_u_name'] = user.fullname
                    c_dict['c_u_key'] = user.key
                    c_dict['c_u_id'] = user.key.id()
                    list_dict.append(c_dict)
            if cookie_user:
                if not post:
                    self.error(404)
                    return
                if cookie_user.key == post.user:
                    self.render("blog.html", post = post,user=cookie_user,
                        comments=list_dict, like_count = no_of_likes,
                        comment_count = comment_count, is_author=True)
                else:
                    self.render("blog.html", post = post,user=cookie_user,
                        comments=list_dict, like_count = no_of_likes,
                        comment_count = comment_count, is_author=False)
            else:
                self.render("blog.html", post = post,user=None,
                    comments=list_dict,like_count = no_of_likes,
                    comment_count = comment_count,is_author=False)
        else:
            self.error(404)
            return

class LikeHandler(BlogHandler):
    def post(self):
        cookie_user = self.get_user_from_cookie()
        if cookie_user:
            postID = self.request.get('postID')
            post_obj = Post.get_by_id(int(postID))
            like_obj = Likes.query(Likes.post == post_obj.key).get()

            if post_obj.user == cookie_user.key:
                self.write(json.dumps(({'like_count': -1})))
            else:
                if like_obj:
                    like_obj.like_count += 1
                    liked_by = like_obj.user_id
                    for u_id in liked_by:
                        if u_id == cookie_user.key.id():
                            self.write(json.dumps(({'like_count': -2})))
                            return
                    liked_by.append(cookie_user.key.id())
                    like_obj.put()
                    self.write(json.dumps(({'like_count': like_obj.like_count})))
                else:
                    like_obj = Likes(post = post_obj.key,like_count=1)
                    like_obj.put()
                    time.sleep(0.2)
                    self.write(json.dumps(({'like_count' : like_obj.like_count})))
        else:
            return None


class CommentHandler(BlogHandler):
    def get(self,comment_id):
        commentObj = Comments.get_by_id(int(comment_id))
        self.write(json.dumps(({'comment': commentObj.comment})))

    def post(self,post_id):
        comment = self.request.get('comment')
        post = Post.get_by_id(int(post_id))
        # user_id = check_for_valid_cookie(self)
        cookie_user = self.get_user_from_cookie()
        if cookie_user:
            if comment:
                comment_obj = Comments(user=cookie_user.key,
                                       post=post.key,
                                       comment=comment)
                comment_obj.put()
                time.sleep(0.2)
                self.redirect('/blog/%s'% post_id)
            else:
                empty_comment = "You can't post an empty content!"
                self.redirect('/blog/%s?empty_comment=True'%post.key.id())
        else:
            cookie_error = 'You have to be logged in to comment!'
            self.render('login.html',cookie_error=cookie_error)


class DeleteCommentHandler(BlogHandler):
    def get(self,post_id,comment_id):
        cookie_user = self.get_user_from_cookie()
        if cookie_user:
            comment = Comments.get_by_id(int(comment_id))
            if comment:
                comment.key.delete()
                time.sleep(0.2)
                self.redirect('/blog/%s'% str(post_id))
            else:
                comment_error = "Sorry the comment doesn't exist!"
                self.redirect('/blog/%s' % post_id)
        else:
            cookie_error = 'You have to be logged in to delete a comment!'
            self.render('login.html',cookie_error=cookie_error)


class EditCommentHandler(BlogHandler):
    def post(self):
        cookie_user = self.get_user_from_cookie()

        if cookie_user:
            post_id = self.request.get('postID')
            comment_id = self.request.get('commentID')
            comment_str = self.request.get('comment_str')
            if post_id and comment_id and comment_str:
                commentObj = Comments.get_by_id(int(comment_id))
                if commentObj:
                    commentObj.comment = comment_str
                    commentObj.put()
                    time.sleep(0.2)
                    commentObj = Comments.get_by_id(int(comment_id))
                    self.write(json.dumps(({'comment_str' : commentObj.comment})))
                    # self.redirect('/blog/%s'%post_id)
                else:
                    self.error(404)
            else:
                self.error(404)
                return
        else:
            cookie_error = 'You have to be logged in to edit a comment!'
            self.render('login.html',cookie_error=cookie_error)

class ProfileHandler(BlogHandler):
    def get(self,user_id):
        # cookie_user_id = check_for_valid_cookie(self)
        user_cookie = self.get_user_from_cookie()
        user_public = User.get_by_id(int(user_id))
        upload_url = blobstore.create_upload_url('/upload')

        if user_cookie:
            if user_cookie.email != user_public.email:
                public_profile = True

                user_photo_obj = UserPhoto.query(UserPhoto.user == user_cookie.key).get()
                if user_photo_obj:
                    if user_photo_obj.photo_blob_key:
                        pic_serving_url = images.get_serving_url(user_photo_obj.photo_blob_key, size=90, crop=True)
                    else:
                        pic_serving_url = '//placehold.it/100'
                else:
                    pic_serving_url = '//placehold.it/100'

                self.render('profile.html',user=user_cookie,
                            user_public=user_public,
                            public_profile= public_profile,
                            pic_serving_url = pic_serving_url)
            else:
                if user_cookie.email:
                    public_profile = False

                    user_photo_obj = UserPhoto.query(UserPhoto.user == user_cookie.key).get()
                    if user_photo_obj:
                        if user_photo_obj.photo_blob_key:
                            pic_serving_url = images.get_serving_url(user_photo_obj.photo_blob_key, size=90, crop=True)
                        else:
                            pic_serving_url = '//placehold.it/100'
                    else:
                        pic_serving_url = '//placehold.it/100'

                    self.render('profile.html',user=user_cookie,
                             user_public=user_public,
                             public_profile= public_profile,
                             upload_url=upload_url,
                             pic_serving_url = pic_serving_url)
                else:
                    cookie_error = 'You need to log in first to edit profile!'
                    self.render('login.html',cookie_error=cookie_error)
        else:
            public_profile = True
            #user_photo_obj = UserPhoto.query(UserPhoto.user == user_cookie.key).get()
            user_photo_obj = None
            if user_photo_obj:
                if user_photo_obj.photo_blob_key:
                    pic_serving_url = images.get_serving_url(user_photo_obj.photo_blob_key, size=90, crop=True)
                else:
                    pic_serving_url = '//placehold.it/100'
            else:
                pic_serving_url = '//placehold.it/100'

            self.render('profile.html',user=user_cookie,
                        user_public=user_public,
                        public_profile= public_profile,
                        pic_serving_url = pic_serving_url)


class PhotoUploadHandler(blobstore_handlers.BlobstoreUploadHandler):
    def post(self):
        logging.debug('Enters PhotoUploadHandler')
        cookie_user = self.get_user_from_cookie()

        if user_cookie:
            user_photo_obj = UserPhoto.query(UserPhoto.user == user_cookie.key).get()
            if user_photo_obj:
                try:
                    upload = self.get_uploads('img')
                    blobInfo = upload[0]
                    user_photo_obj.photo_blob_key = blobInfo.key
                    user_photo_obj.put()
                    time.sleep(0.2)
                    self.redirect('/profile/%s'% user_cookie.key.id())
                except:
                    self.error(500)
            else:
                try:
                    upload = self.get_uploads('img')
                    blobInfo = upload[0]
                    user_photo = UserPhoto(
                        user= user_cookie.key,
                        photo_blob_key=blobInfo.key()
                    )
                    user_photo.put()
                    time.sleep(0.2)
                    self.redirect('/profile/%s'%user_cookie.key.id())
                except:
                    logging.error('Error uploading')
                    self.error(500)
        else:
            cookie_error = 'You need to log in first to edit profile!'
            self.render('login.html',cookie_error=cookie_error)


class EditPersonalInfoHandler(BlogHandler):
    def post(self):
        fullname = self.request.get('fullname')
        about = self.request.get('about')
        location = self.request.get('location')

        user_cookie = self.get_user_from_cookie()

        if user_cookie:
            user_cookie.fullname = fullname
            user_cookie.about = about
            user_cookie.location = location

            user_cookie.put()
            time.sleep(0.1)
            self.redirect('/profile/%s?updated=True'% str(user_cookie.key.id()))
            # details_updated = "Details were updated successfully!"
            # self.render('profile.html',user=user_cookie,user_public=False,
            #     public_profile= False,details_updated=details_updated)
        else:
            cookie_error = 'You need to log in first to edit your profile!'
            self.render('login.html',cookie_error=cookie_error)


class ChangePassHandler(BlogHandler):
    def post(self):
        password = self.request.get('password')
        confirm_pass = self.request.get('confirm_pass')

        cookie_user = self.get_user_from_cookie()

        if cookie_user:
            if password == confirm_pass:
                if valid_password(password):
                    user_cookie.password = hash_str(password)
                    user_cookie.put()
                    time.sleep(0.1)
                    self.redirect('/profile/%s?pass_update=True'% str(user_cookie.key.id()))
                else:
                    self.redirect('/profile/%s?pass_update=False'% str(user_cookie.key.id()))
            else:
                self.redirect('/profile/%s?pass_update=False'% str(user_cookie.key.id()))
        else:
            cookie_error = 'You need to log in first to edit profile!'
            self.render('login.html',cookie_error=cookie_error)


# class PhotoUploadHandler(BlogHandler, blobstore_handlers.BlobstoreUploadHandler):
#     def post(self):
#         user_email = check_for_valid_cookie(self)
#         user_cookie = User.query(User.email == user_email).get()
#         user_photo = UserPhoto.query(UserPhoto.user == user_cookie.key).get()

#         if user_cookie:
#             img = self.request.get('img')
#             img = images.resize(img, 32, 32)
#             user_photo = UserPhoto(user=user_cookie.key,
#                                    photo_blob = img)
#             #serving_url = image.get_serving_url()
#             user_photo.put()
#             time.sleep(0.1)
#             self.redirect('/profile/%s?up=%s'% (str(user_cookie.key.id()),str(user_photo.key.id())))

#             # upload = self.get_uploads()[0]
#             # user_photo = UserPhoto(
#             #     user=user_cookie.key,
#             #     photo_blob_key=upload.key())
#             # user_photo.put()
#             # time.sleep(0.1)
#             # self.redirect('/profile/%s'% str(user_cookie.key.id()))
#             # self.redirect('/view_photo/%s' % upload.key())
#         else:
#             cookie_error = 'You need to log in first to edit profile!'
#             self.render('login.html',cookie_error=cookie_error)

class AboutUsHandler(BlogHandler):
    def get(self):
        cookie_user = self.get_user_from_cookie()
        self.render('aboutus.html',user=cookie_user)

class TestHandler(BlogHandler):
    def get(self):
        loggedin_user = self.get_user_from_cookie()
        all_users = User.query()
        posts = Post.query()
        comments = Comments.query().order(-Comments.comment_date)

        # for each_user in all_users:
        #     each_post = Post.query(Post.user == each_user.key).fetch()
        #     posts.append(each_post)

        # for post in posts:
        #     return self.write(post)

        # for each_user_from_db in ndb.gql('select * from User'):
        #     for post in ndb.gql('select * from Post where user=:1',each_user_from_db.key):
        #         all_users = each_user_from_db
        #         posts.append(post)

        from_zone = tz.tzutc()
        to_zone = tz.tzlocal()
        post = Post.get_by_id(5642556234792960)

        date_utc = post.created
        date_utc = date_utc.replace(tzinfo=from_zone)

        localtz = date_utc.astimezone(to_zone)

        self.write("Post created UTC : %s" % post.created)
        self.write("<br>")
        self.write("<br>")
        self.write("Post Local : %s" % localtz)

        return self.render('test.html',user=loggedin_user,
                                       all_users=all_users,
                                       posts=posts,
                                       comments=comments)

    def post(self):
        loggedin_user = self.get_user_from_cookie()
        all_users = User.query()
        posts = Post.query()

        post_id = self.request.get('post_id')
        like_count = self.request.get('like_count')

        post = Post.get_by_id(int(post_id))

        if post:
            new_like_object = Likes(post = post.key, like_count = int(like_count))
            key = new_like_object.put()
            time.sleep(0.1)
            new_like = key.get()
            post_key = new_like.post
            post = post_key.get()
            self.write("Like Count: " + str(new_like.like_count) + "Post Title:" + post.Title)


class AllPostsHandler(BlogHandler):
    def get(self):
        cookie_user = self.get_user_from_cookie()
        posts = Post.query(Post.is_draft== False).order(-Post.created)

        return self.render('allposts.html',user=cookie_user, posts=posts)

class DraftPostsHandler(BlogHandler):
    def get(self,user_id):
        cookie_user = self.get_user_from_cookie()

        if cookie_user:
            posts = Post.query(ndb.AND(Post.is_draft == True,Post.user == cookie_user.key)).order(-Post.created)
            self.render('draftposts.html',user=cookie_user, posts=posts)
        else:
            cookie_error = 'You need to be logged in to view your drafts!'
            self.render('login.html',cookie_error=cookie_error)


class ViewDraftHandler(BlogHandler):
    def get(self,post_id):
        post = Post.get_by_id(int(post_id))
        cookie_user = self.get_user_from_cookie()

        if cookie_user:
            if post:
                delete_draft = self.request.get('draft_delete')
                self.render('viewdraftpost.html',user = cookie_user,
                    post = post, delete_draft=delete_draft)
            else:
                self.error(404)
                return
        else:
            cookie_error = 'You need to be logged in to view your drafts!'
            self.render('login.html',cookie_error=cookie_error)


class EditDraftHandler(BlogHandler):
    def get(self,post_id):
        cookie_user = self.get_user_from_cookie()
        post = Post.get_by_id(int(post_id))

        if cookie_user:
            if post:
                self.render('editdraft.html',user=cookie_user,
                    post=post)
            else:
                self.error(404)
                return
        else:
            cookie_error = "You need to log in before you edit the post!"
            self.render('login.html',cookie_error = cookie_error)

    def post(self,post_id):
        cookie_user = self.get_user_from_cookie()

        if cookie_user:
            post = Post.get_by_id(int(post_id))
            if post:
                postTitle = self.request.get('post-title')
                postContent = self.request.get('content')
                is_draft = self.request.get('draft')

                if is_draft == 'on':
                    is_draft = True
                    if postTitle and postContent:
                        post.title = postTitle
                        post.content = postContent
                        post.is_draft = is_draft
                        post.put()
                        time.sleep(0.2)
                        #self.redirect('/home')
                        self.redirect('/draft/%s'% post.key.id())
                    else:
                        empty_title_content = True
                        self.render('editdraft.html',user=cookie_user,
                            post=post,empty_title_content=empty_title_content)
                else:
                    is_draft = False
                    post.title = postTitle
                    post.content = postContent
                    post.is_draft = is_draft
                    post.put()
                    time.sleep(0.2)
                    self.redirect('/blog/%s'%post.key.id())
            else:
                self.error(404)
                return
        else:
            cookie_error = "You need to log in before you edit your draft!"
            self.render('login.html',cookie_error = cookie_error)

class DeleteDraftHandler(BlogHandler):
    def get(self,post_id):
        cookie_user = self.get_user_from_cookie()
        post = Post.get_by_id(int(post_id))

        if cookie_user:
            if post:
                self.render('deletedraft.html',user=cookie_user,post=post)
            else:
                self.error(404)
                return
        else:
            cookie_error = "You need to log in before you delete a draft!"
            self.render('login.html',cookie_error = cookie_error)

    def post(self,post_id):
        cookie_user = self.get_user_from_cookie()

        if cookie_user:
            post = Post.get_by_id(int(post_id))
            if post:
                post.key.delete()
                time.sleep(0.2)
                self.redirect('/user/%s/drafts?draft_delete=True'%cookie_user.key.id())
            else:
                self.error(404)
                return
        else:
            cookie_error = "You need to log in before you delete the post!"
            self.render('login.html',cookie_error = cookie_error)

class PostDraftHandler(BlogHandler):
    def get(self,post_id):
        cookie_user = self.get_user_from_cookie()
        post = Post.get_by_id(int(post_id))

        if cookie_user:
            if post:
                post.is_draft = False
                post.created = datetime.now()
                post.put()
                time.sleep(0.2)
                self.redirect('/blog/%s'% post.key.id())
            else:
                self.error(404)
                return
        else:
            cookie_error = "You need to log in before you post a draft to public!"
            self.render('login.html',cookie_error = cookie_error)


class ForgetPasswordHandler(BlogHandler):
    def post(self):
        email = self.request.get('email');
        if email:
            user = User.query(User.email == email).get()
            if user:
                message = mail.EmailMessage(
                        sender="Support @ Your Own Blog <abhighosh18@gmail.com>",
                        subject="Your account has been approved")

                message.to = "%s <%s>" % (user.fullname, email),

                message.html = """
            <html><head></head><body>
            Dear %s:

            <p>Your example.com account has been approved.  You can now visit
            <a href="your-own-blog.appspot.com/home">My Home</a> and sign in using your Google Account to
            access new features.</p>

            <p>Please let us know if you have any questions.</p>

            The Your Own Blog Team
            </body></html>
            """ % user.fullname
                message.send()
                self.write(json.dumps(({'result': 'success'})))
            else:
                self.write(json.dumps(({'result': 'invalid_email'})))
        else:
            self.write(json,dumps(({'result': 'empty_email'})))


app = webapp2.WSGIApplication([
    ('/', HomeHandler),
    ('/home', HomeHandler),
    ('/login', LoginHandler),
    ('/register',RegistrationHandler),
    ('/logout', LogOutHandler),
    ('/aboutus',AboutUsHandler),
    ('/newpost',NewPostHandler),
    ('/blog/([0-9]+)', PostPageHandler),
    ('/profile/([0-9]+)',ProfileHandler),
    ('/personalinfo',EditPersonalInfoHandler),
    ('/changepass',ChangePassHandler),
    ('/upload',PhotoUploadHandler),
    ('/voteup',LikeHandler),
    ('/comment/([0-9]+)', CommentHandler),
    ('/comment/([0-9]+)/delete/([0-9]+)', DeleteCommentHandler),
    ('/editcomment',EditCommentHandler),
    ('/editblog/([0-9]+)', EditBlogHandler),
    ('/deleteblog/([0-9]+)', DeleteBlogHandler),
    ('/allposts', AllPostsHandler),
    ('/user/([0-9]+)/drafts', DraftPostsHandler),
    ('/draft/([0-9]+)/edit', EditDraftHandler),
    ('/draft/([0-9]+)/delete', DeleteDraftHandler),
    ('/draft/([0-9]+)', ViewDraftHandler),
    ('/draft/([0-9]+)/post', PostDraftHandler),
    ('/forgetpassword', ForgetPasswordHandler),
    ('/test',TestHandler)
], debug=True)
