import time
from base_handler import BlogHandler
from models import User
from utility import valid_email, valid_username, valid_password, hash_str

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
                    Try another username!')
                has_error = True

            if has_error:
                self.render('register.html', fullname=fullname,
                            location=location,
                            email=email,
                            user_name=u_name,
                            error_list=error_list)
            else:
                new_user = User(fullname=fullname,
                                location=location,
                                email=email,
                                user_name=u_name,
                                password=hash_str(password))
                new_user_key = new_user.put()

                # new_user_photo_obj = UserPhoto(user=new_user_key)
                # new_user_photo_obj.put()

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
                self.render('login.html', new_user=new_user.fullname)
        else:
            error_list.append("You did not fill atleast one of the fields!")
            self.render('register.html', fullname=fullname,
                        location=location,
                        email=email,
                        user_name=u_name,
                        error_list=error_list)
