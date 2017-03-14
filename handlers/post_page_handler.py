from base_handler import BlogHandler
from models import User, Post, Comments, Likes

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
                    self.render("blog.html",
                                post=post,
                                user=cookie_user,
                                comments=list_dict,
                                like_count=no_of_likes,
                                comment_count=comment_count,
                                is_author=True)
                else:
                    self.render("blog.html",
                                post=post,
                                user=cookie_user,
                                comments=list_dict,
                                like_count=no_of_likes,
                                comment_count=comment_count,
                                is_author=False)
            else:
                self.render("blog.html",
                            post=post,
                            user=None,
                            comments=list_dict,
                            like_count=no_of_likes,
                            comment_count=comment_count,
                            is_author=False)
        else:
            self.error(404)
            return
