import hashlib
import hmac
from hash_keys import SECRET

def hash_str(password):
    return hmac.new(SECRET, password).hexdigest()

def make_secure_val(password):
    return "%s|%s" % (password, hash_str(password))

def check_secure_val(hash_value):
    val = hash_value.split("|")[0]
    if hash_value == make_secure_val(val):
        return val
