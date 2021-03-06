import os
import webapp2
import jinja2
import json
import time
import logging

from utility import check_secure_val, hash_str, make_secure_val,\
                    valid_username, valid_password, valid_email
from models import User, Post, UserPhoto, Likes, Comments
from utility import showCount, filterKey
from handlers import BlogHandler, HomeHandler, LoginHandler, LogOutHandler,\
                     RegistrationHandler, NewPostHandler, EditBlogHandler, \
                     DeleteBlogHandler, PostPageHandler, AboutMeHandler

from datetime import datetime
from dateutil import tz
from google.appengine.ext import ndb
from google.appengine.api import mail
from google.appengine.api import app_identity
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.ext import blobstore
from google.appengine.api import images

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
                    liked_by = like_obj.user_id
                    for u_id in liked_by:
                        if u_id == cookie_user.key.id():
                            self.write(json.dumps(({'like_count': -2})))
                            return
                    like_obj.like_count += 1
                    liked_by.append(cookie_user.key.id())
                    like_obj.put()
                    self.write(json.dumps(({'like_count': like_obj.like_count})))
                else:
                    like_obj = Likes(post=post_obj.key, like_count=1)
                    like_obj.user_id.append(cookie_user.key.id())
                    like_obj.put()
                    time.sleep(0.2)
                    self.write(json.dumps(({'like_count' : like_obj.like_count})))
        else:
            return None


class CommentHandler(BlogHandler):
    def get(self, comment_id):
        commentObj = Comments.get_by_id(int(comment_id))
        self.write(json.dumps(({'comment': commentObj.comment})))

    def post(self, post_id):
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
            self.render('login.html', cookie_error=cookie_error)


class DeleteCommentHandler(BlogHandler):
    def get(self, post_id, comment_id):
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
            self.render('login.html', cookie_error=cookie_error)


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
            self.render('login.html', cookie_error=cookie_error)

class ProfileHandler(BlogHandler):
    def get(self, user_id):
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
                        pic_serving_url = images.get_serving_url( \
                                          user_photo_obj.photo_blob_key, size=90, crop=True)
                    else:
                        pic_serving_url = '//placehold.it/100'
                else:
                    pic_serving_url = '//placehold.it/100'

                self.render('profile.html',
                            user=user_cookie,
                            user_public=user_public,
                            public_profile=public_profile,
                            pic_serving_url=pic_serving_url)
            else:
                if user_cookie.email:
                    public_profile = False
                    user_photo_obj = UserPhoto.query(UserPhoto.user == user_cookie.key).get()
                    if user_photo_obj:
                        if user_photo_obj.photo_blob_key:
                            pic_serving_url = images.get_serving_url( \
                                              user_photo_obj.photo_blob_key, size=90, crop=True)
                        else:
                            pic_serving_url = '//placehold.it/100'
                    else:
                        pic_serving_url = '//placehold.it/100'

                    self.render('profile.html',
                                user=user_cookie,
                                user_public=user_public,
                                public_profile=public_profile,
                                upload_url=upload_url,
                                pic_serving_url=pic_serving_url)
                else:
                    cookie_error = 'You need to log in first to edit profile!'
                    self.render('login.html', cookie_error=cookie_error)
        else:
            public_profile = True
            #user_photo_obj = UserPhoto.query(UserPhoto.user == user_cookie.key).get()
            user_photo_obj = None
            if user_photo_obj:
                if user_photo_obj.photo_blob_key:
                    pic_serving_url = images.get_serving_url( \
                                      user_photo_obj.photo_blob_key, size=90, crop=True)
                else:
                    pic_serving_url = '//placehold.it/100'
            else:
                pic_serving_url = '//placehold.it/100'

            self.render('profile.html',
                        user=user_cookie,
                        user_public=user_public,
                        public_profile=public_profile,
                        pic_serving_url=pic_serving_url)


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
                        user=user_cookie.key,
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
            self.render('login.html', cookie_error=cookie_error)


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
            self.render('login.html', cookie_error=cookie_error)


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
            self.render('login.html', cookie_error=cookie_error)


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

        return self.render('test.html',
                           user=loggedin_user,
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
            new_like_object = Likes(post=post.key, like_count=int(like_count))
            key = new_like_object.put()
            time.sleep(0.1)
            new_like = key.get()
            post_key = new_like.post
            post = post_key.get()
            self.write("Like Count: " + str(new_like.like_count) + "Post Title:" + post.Title)


class AllPostsHandler(BlogHandler):
    def get(self):
        cookie_user = self.get_user_from_cookie()
        posts = Post.query(Post.is_draft == False).order(-Post.created)

        return self.render('allposts.html', user=cookie_user, posts=posts)

class DraftPostsHandler(BlogHandler):
    def get(self, user_id):
        cookie_user = self.get_user_from_cookie()

        if cookie_user:
            posts = Post.query(ndb.AND \
                              (Post.is_draft == True, Post.user == cookie_user.key)) \
                              .order(-Post.created)
            self.render('draftposts.html', user=cookie_user, posts=posts)
        else:
            cookie_error = 'You need to be logged in to view your drafts!'
            self.render('login.html', cookie_error=cookie_error)


class ViewDraftHandler(BlogHandler):
    def get(self, post_id):
        post = Post.get_by_id(int(post_id))
        cookie_user = self.get_user_from_cookie()

        if cookie_user:
            if post:
                delete_draft = self.request.get('draft_delete')
                self.render('viewdraftpost.html',
                            user=cookie_user,
                            post=post,
                            delete_draft=delete_draft)
            else:
                self.error(404)
                return
        else:
            cookie_error = 'You need to be logged in to view your drafts!'
            self.render('login.html', cookie_error=cookie_error)


class EditDraftHandler(BlogHandler):
    def get(self, post_id):
        cookie_user = self.get_user_from_cookie()
        post = Post.get_by_id(int(post_id))

        if cookie_user:
            if post:
                self.render('editdraft.html',
                            user=cookie_user,
                            post=post)
            else:
                self.error(404)
                return
        else:
            cookie_error = "You need to log in before you edit the post!"
            self.render('login.html', cookie_error=cookie_error)

    def post(self, post_id):
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
                        self.render('editdraft.html',
                                    user=cookie_user,
                                    post=post,
                                    empty_title_content=empty_title_content)
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
            self.render('login.html', cookie_error=cookie_error)

class DeleteDraftHandler(BlogHandler):
    def get(self, post_id):
        cookie_user = self.get_user_from_cookie()
        post = Post.get_by_id(int(post_id))

        if cookie_user:
            if post:
                self.render('deletedraft.html', user=cookie_user, post=post)
            else:
                self.error(404)
                return
        else:
            cookie_error = "You need to log in before you delete a draft!"
            self.render('login.html', cookie_error=cookie_error)

    def post(self, post_id):
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
            self.render('login.html', cookie_error=cookie_error)

class PostDraftHandler(BlogHandler):
    def get(self, post_id):
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
            self.render('login.html', cookie_error=cookie_error)


class ForgetPasswordHandler(BlogHandler):
    def post(self):
        email = self.request.get('email')
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
            self.write(json.dumps(({'result': 'empty_email'})))


class MyPostsHandler(BlogHandler):
    def get(self, user_id):
        self.render('page_under_construction.html')


def handle_404(request, response, exception):
    logging.warn(str(exception))
    response.set_status(404)
    handler = BlogHandler(request, response)
    handler.render("404.html");


app = webapp2.WSGIApplication([
    ('/', HomeHandler),
    ('/home', HomeHandler),
    ('/login', LoginHandler),
    ('/register', RegistrationHandler),
    ('/logout', LogOutHandler),
    ('/about', AboutMeHandler),
    ('/newpost', NewPostHandler),
    ('/blog/([0-9]+)', PostPageHandler),
    ('/profile/([0-9]+)', ProfileHandler),
    ('/personalinfo', EditPersonalInfoHandler),
    ('/changepass', ChangePassHandler),
    ('/upload', PhotoUploadHandler),
    ('/voteup', LikeHandler),
    ('/comment/([0-9]+)', CommentHandler),
    ('/comment/([0-9]+)/delete/([0-9]+)', DeleteCommentHandler),
    ('/editcomment', EditCommentHandler),
    ('/editblog/([0-9]+)', EditBlogHandler),
    ('/deleteblog/([0-9]+)', DeleteBlogHandler),
    ('/allposts', AllPostsHandler),
    ('/user/([0-9]+)/drafts', DraftPostsHandler),
    ('/draft/([0-9]+)/edit', EditDraftHandler),
    ('/draft/([0-9]+)/delete', DeleteDraftHandler),
    ('/draft/([0-9]+)', ViewDraftHandler),
    ('/draft/([0-9]+)/post', PostDraftHandler),
    ('/forgetpassword', ForgetPasswordHandler),
    ('/user/([0-9]+)/myposts', MyPostsHandler),
    ('/test', TestHandler)
], debug=True)

app.error_handlers[404] = handle_404
