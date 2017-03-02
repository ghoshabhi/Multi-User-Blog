import hashlib
import hmac
import re
from hash_keys import SECRET

def hash_str(password):
    return hmac.new(SECRET, password).hexdigest()

def make_secure_val(password):
    return "%s|%s" % (password, hash_str(password))

def check_secure_val(hash_value):
    val = hash_value.split("|")[0]
    if hash_value == make_secure_val(val):
        return val

USERNAME_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
def valid_username(username):
    return username and USERNAME_RE.match(username)


PASS_RE = re.compile(r"^.{3,20}$")
def valid_password(password):
    return password and PASS_RE.match(password)


EMAIL_RE = re.compile(r'^[\S]+@[\S]+\.[\S]+$')
def valid_email(email):
    return not email or EMAIL_RE.match(email)
