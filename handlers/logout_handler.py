from base_handler import BlogHandler

class LogOutHandler(BlogHandler):
    def get(self):
        self.response.headers.add_header('Set-Cookie', 'random=''')
        thank_you_for_visiting = "Thank you for visiting this site.\
            We appreciate your presence!"
        self.render('login.html', thank_you_for_visiting=thank_you_for_visiting)
