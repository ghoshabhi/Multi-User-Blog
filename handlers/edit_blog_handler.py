import time
from base_handler import BlogHandler
from models import Post

class EditBlogHandler(BlogHandler):
    def get(self, post_id):
        # user_id = check_for_valid_cookie(self)
        # cookie_user = User.get_by_id(int(user_id))
        cookie_user = self.get_user_from_cookie()
        post = Post.get_by_id(int(post_id))

        if cookie_user:
            if post:
                self.render('editpost.html', user=cookie_user,
                            post=post)
            else:
                #self.error(404)
                self.render("error.html")
                return
        else:
            cookie_error = "You need to log in before you edit the post!"
            self.render('login.html', cookie_error=cookie_error)

    def post(self, post_id):
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
                    self.render('editpost.html', user=cookie_user,
                                post=post, empty_title_content=empty_title_content)
            else:
                self.error(404)
                return
        else:
            cookie_error = "You need to log in before you edit the post!"
            self.render('login.html', cookie_error=cookie_error)
