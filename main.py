from flask import Flask,render_template,request,session,redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_mail import Mail
from werkzeug.utils import secure_filename
import os
import math
import json
import pymysql
pymysql.install_as_MySQLdb()


with open('config.json','r') as c:
    params1 = json.load(c)["params"]


local_server = True

# it defines app
app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = params1['upload_location']

app.secret_key = "super-secret-key"     # we can write anything in place of super secret key

app.config.update(
    MAIL_SERVER = "smtp.gmail.com",
    MAIL_PORT = "465",
    MAIL_USE_SSL = "True",
    MAIL_USERNAME = params1['gmail-user'],
    MAIL_PASSWORD = params1['gmail-password']
)

mail = Mail(app)

if local_server:
    app.config['SQLALCHEMY_DATABASE_URI'] = params1['local_uri']      # username = root, password = blank, db_name = codingthunder
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params1['prod_uri']


db = SQLAlchemy(app)                   # initialisation


# This class will define the tables of the database
class Contacts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(20),nullable=False)
    phone_num = db.Column(db.String(12),nullable=False)
    msg = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)


class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    tagline = db.Column(db.String(120), nullable=False)
    slug = db.Column(db.String(25),nullable=False)
    content = db.Column(db.String(120),nullable=False)
    date = db.Column(db.String(12), nullable=True)
    img_file = db.Column(db.String(12), nullable=True)


@app.route('/')                           # if we write nothing else it will return index.html
def home():                               # it's like an end point.
    posts = Posts.query.filter_by().all()
    last = math.ceil(len(posts)/int(params1['no_of_posts']))
    page = request.args.get('page')

    if not str(page).isnumeric():
        page = 1

    page = int(page)
    posts = posts[(page-1)*int(params1['no_of_posts']): (page-1)*int(params1['no_of_posts'])+int(params1['no_of_posts'])]

    # Paginaton Logic
    # First page
    if page == 1:
        prev = "#"
        next = "/?page="+str(page+1)

    # Last Page
    elif page == last:
        prev = "/?page="+str(page-1)
        next = "#"

    # Middle Page
    else:
        prev = "/?page=" + str(page - 1)
        next = "/?page=" + str(page + 1)

    return render_template('index.html', params=params1, posts=posts, prev=prev, next=next)


@app.route('/about')
def about():
    return render_template('about.html',params=params1)


@app.route('/dashboard', methods=['GET','POST'])
def dashboard():

    # if the user is already logged in
    if 'user' in session and session['user']==params1['admin_username']:
        posts = Posts.query.all()
        return render_template('dashboard.html',params=params1,posts=posts)

    # redirect to admin panel
    if request.method=='POST':
        username=request.form.get('uname')
        userpass=request.form.get('pass')
        if username==params1['admin_username'] and userpass==params1['admin_password']:
            # set the session variable
            session['user'] = username
            posts = Posts.query.all()
            return render_template('dashboard.html', params=params1,posts=posts)
        else:
            return render_template('login.html', params=params1)

    else:
        return render_template('login.html', params=params1)


@app.route('/post/<string:post_slug>', methods=['GET'])
def post_route(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    return render_template('post.html',params=params1,post=post)


@app.route('/edit/<string:sno>', methods=['GET','POST'])
def edit(sno):
    # Check if the user is logged in or not
    if 'user' in session and session['user'] == params1['admin_username']:
        if request.method == "POST":
            box_title = request.form.get('title')
            box_tagline = request.form.get('tline')
            box_slug = request.form.get('slug')
            box_content = request.form.get('content')
            box_imgfile = request.form.get('img_file')

            # Add new post
            if sno=='0':
                post = Posts(title=box_title, tagline=box_tagline, slug=box_slug, content=box_content, img_file=box_imgfile, date=datetime.now())
                db.session.add(post)
                db.session.commit()

            else:
                post = Posts.query.filter_by(sno=sno).first()
                post.title = box_title
                post.tagline = box_tagline
                post.slug = box_slug
                post.content = box_content
                post.img_file = box_imgfile
                post.date = datetime.now()
                db.session.commit()
                return redirect('/edit/'+sno)

        post = Posts.query.filter_by(sno=sno).first()
        return render_template('edit.html',params=params1, post=post)


@app.route('/uploader', methods=['GET', 'POST'])
def uploader():
    if 'user' in session and session['user'] == params1['admin_username']:
        if request.method == "POST":
            f = request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
            return "Uploaded Successfully"


@app.route('/logout')
def logout():
    session.pop('user')
    return redirect('/dashboard')


@app.route('/delete/<string:sno>', methods=['GET','POST'])
def delete(sno):
    if 'user' in session and session['user'] == params1['admin_username']:
        post = Posts.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()

    return redirect('/dashboard')


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == "POST":
        # Fetching entry
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')

        # Add entry to the database
        entry = Contacts(name=name, phone_num=phone, msg=message, date=datetime.now(), email=email)
        db.session.add(entry)
        db.session.commit()
        mail.send_message('New message from' + name,
                          sender=email,
                          recipients=[params1['gmail-user']],
                          body=message + "\n" + phone
                          )
    return render_template('contact.html',params=params1)


app.run(debug=True)
