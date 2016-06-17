# Multi User Blog
------
 The Multi-User Blog site is a blogging website where people can write blogs about their favourite topics. Registered users can _"Like"_ & _"Comment"_ on the posts. The live site can be visited here: your-own-blog.appspot.com

# Table of Contents
-----
1. [Authors and Contributors](#author)
2. [How to deploy the app?](#deploy-app)
3. [Directory Structure](#directory-structure)
4. [Resources Used](#resources)
5. [Future Improvements](#future-improvements)

<br><br>
### <a name="author"></a>1. Authors and Contributors
--------------------
I, [Abhishek Ghosh](https://github.com/ghoshabhi) am the developer for this site. Also, there were major contributions from [Ian Gristoi](https://github.com/gristoi) and [Abigail Mathews](https://github.com/AbigailMathews). I thank them for their contributions to the site! 
<br>
<br>
<br>
### <a name="deploy-app"></a>2. How to deploy the app ?
---------------
Follow the steps below to run the app :

1. Download Google App Engine Console
2. Clone the repository from https://github.com/ghoshabhi/Multi-User-Blog.git
3. To run locally : 
	* Unzip the contents from the cloned directory and find the file _"app.yaml"_.
	* Open the app engine console and choose the option _"Add an existing application"_ from the Menu bar.
	* Navigate to the location where the repo was cloned.
	* Click the *_"Run"_* button and navigate to the port mentioned for the app in the app engine console. If this is the first time you're running the app you will have the site open at : localhost:8080
4. If you want to visit the live hosted app, visit this URL : your-own-blog.appspot.com


### <a name="directory-structure"></a>3. Directory Structure
--------------
```
-static
	-contains all the CSS,JS files
-templates
	-contains all the template(.html) files
-app.yaml
-favicon.ico
-find_utf8.py
-index.yaml
-main.py
-models.py
-README.md
```

1. **static :** This folder contains all the CSS/JS/Image files
2. **templates :** This folder contains all the template files.
3. **app.yaml :** Has all the app configurations
4. **favicon.ico :** The website icon seen in the tab 
5. **find_utf8.py :** Utility script written to remove the UTF8 characters from a file
6. **index.yaml :** Contains index definitions
7. **main.py :** Contains the application logic and all the handler definitions
8. **models.py :** Contains all the model definitions 
9. **README.md :** README file


<br><br>
### <a name="resources"></a> 4. Resources
-------
* Python is used as the scripting language for the server
* `jinja2`, a templating library for Python & natively implemented in Google App Engine
`webapp2`, GAE's main library
* `ndb` : The Google Datastore NDB Client Library allows App Engine Python apps to connect to Cloud Datastore. 
* `hmac`, `hlib` to enable encryption
* `re` to enable Regular Expression check for email and password inputs

* Front-end frameworks : HTML,CSS, jQuery, clippy.js, TinyMCE editor, toastr.js

* App Engine : Google App Engine (GAE), Google's platform as a service solution

<br><br>

### <a name="future-improvements"></a> 5. Future Improvements
-----
* Use `ndb.BlobKeyProperty` for Photo uploads
* Implement `tags` for each post
* Show posts according to dates
* Filter by `tags`, `dates` and `author`

_Any suggestions to the site are welcomed. Please email me at abhighosh18@gmail.com to share your suggestions_