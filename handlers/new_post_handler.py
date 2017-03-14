import time
from base_handler import BlogHandler
from models import Post, User, Likes

class NewPostHandler(BlogHandler):
    def get(self):
        cookie_user = self.get_user_from_cookie()
        if cookie_user:
            self.render('newpost.html', user=cookie_user)
        else:
            cookie_error = "Your session has expired please login again to continue!"
            self.render('login.html', cookie_error=cookie_error)

    def post(self):
        cookie_user = self.get_user_from_cookie()
        if cookie_user:
            content = self.request.get('content')
            title = self.request.get('post-title')
            is_draft = self.request.get('draft')

            if is_draft == 'on':
                is_draft = True
            else:
                is_draft = False

            if title != 'Click here to give a Title!' and \
             content != '<p>Start writing here...</p>':
                new_post = Post(
                    title=title,
                    content=content,
                    user=cookie_user.key,
                    is_draft=is_draft
                    )
                new_post_key = new_post.put()
                time.sleep(0.3)
                like_obj = Likes(post=new_post_key, like_count=0)
                like_key = like_obj.put()
                time.sleep(0.1)

                if is_draft:
                    self.redirect('/user/%s/drafts' % str(cookie_user.key.id()))
                else:
                    self.redirect('/blog/%s' % str(new_post_key.id()))
            else:
                empty_post = "Both Title and Content needed for the Blog!"
                self.render('newpost.html', user=cookie_user,
                            title=title, content=content, empty_post=empty_post)
        else:
            cookie_error = "Your session has expired please login again to continue!"
            self.render('login.html', cookie_error=cookie_error)

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
