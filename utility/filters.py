from models import Likes

def filterKey(key):
    return key.id()

def showCount(post_key):
    like_obj = Likes.query(Likes.post == post_key).get()
    if like_obj:
        return like_obj.like_count
    else:
        return "0"
