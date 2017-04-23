from base_handler import BlogHandler
from models import User, Likes, Post, Comments

class HomeHandler(BlogHandler):
    def get(self):
        posts = []
        cookie_user = self.get_user_from_cookie()
        if cookie_user:
            print "cookie_user found: ", cookie_user.username
            loggedin_user = cookie_user
        else:
            print "cookie_user not found"
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

        return self.render('home.html', user=loggedin_user,
                           list_dict=list_dict)
