#!/usr/bin/env python

import time



# define the classes associated with the tables...
class BlogArticle(object):
    def __init__(self, blog_id, article_url, title, feed, article):
        self.blog_id        = blog_id       # parent feed ID
        self.article_url    = article_url     
        self.title          = title           
        self.content        = content            
        self.article        = article         

        # a vector is created by Postgres, not by this code, but we might want to look at it if we read the record.
        self.article_vector = None          
        
    def __repr__(self):
       return "<BlogArticle(%s, %s, '%s', '%s', '%s', %s)>" % (self.id, self.blog_id, self.article_url, self.title, self.feed, self.article)

class BlogFeed(object):
    def __init__(self, url, updated_at=time.localtime(), enabled=False):
        self.url        = url        
        self.updated_at = updated_at 
        self.enabled    = enabled    
        
        self.created_on = time.strftime('%c', time.localtime())
        
    def __repr__(self):
        return "<BlogFeed(%s, '%s', '%s', '%s', '%s')>" % (self.id, self.url, self.created_on, self.updated_at, self.enabled)




# def connect_to_db(db_url=DB_CONNECTION_URL, echo_=True, **options_):    
#     # options_['echo'] = echo_
#     
#     # connect to the database...
#     return create_engine(db_url, echo=echo_, **options_)



