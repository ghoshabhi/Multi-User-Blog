import time
from base_handler import BlogHandler

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
