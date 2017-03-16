from base_handler import BlogHandler

class AboutMeHandler(BlogHandler):
    def get(self):
        self.render('page_under_construction.html')
