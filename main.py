from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from werkzeug import secure_filename
import math
import json
from datetime import datetime
import pymysql
pymysql.install_as_MySQLdb()
import os



with open('config.json', 'r') as c:
    params = json.load(c)["params"]
name="uname"
local_server = True
app = Flask(__name__)
app.secret_key = 'super secret key'
app.config['UPLOAD_FOLDER'] = params['upload_location']
app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = '465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params['gmail-user'],
    MAIL_PASSWORD=  params['gmail-password']
)
mail = Mail(app)
if(local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']

db = SQLAlchemy(app)


class Contacts(db.Model):
    srno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    phone_num = db.Column(db.String(12), nullable=False)
    msg = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    email = db.Column(db.String(20), nullable=False)


class Posts(db.Model):
    srno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    slug = db.Column(db.String(21), nullable=False)
    content = db.Column(db.String(120), nullable=False)
    tagline = db.Column(db.String(12), nullable=True)
    date = db.Column(db.String(12), nullable=True)
    img_file = db.Column(db.String(12), nullable=True)


@app.route("/")
def home():
    posts = Posts.query.filter_by().all()
    # [0:params['no_of_posts']]
    last=math.ceil(len(posts)/int(params['no_of_posts']))
    # posts=posts[]
    page = request.args.get('page')
    if(not str(page).isnumeric()):
        page = 1
    page = int(page)
    posts=posts[(page-1)*int(params['no_of_posts']):(page-1)*int(params['no_of_posts']) + int(params['no_of_posts'])]
    if (page == 1):
        prev='#'
        next='/?page=' + str(page + 1)


    elif (page == last):
        prev='/?page=' + str(page - 1)
        next='#'

    else:
        prev='/?page=' + str(page - 1)
        next='/?page=' + str(page + 1)




    return render_template('index.html', params=params, posts=posts, prev=prev, next=next)


@app.route("/post/<string:post_slug>", methods=['GET'])
def post_route(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    return render_template('post.html', params=params, post=post)

@app.route("/about")
def about():
    return render_template('about.html', params=params)

@app.route("/dashboard", methods=['GET','POST'])
def dashboard():
    if 'user' in session and session['user'] == params['admin_user']:
        posts = Posts.query.all()
        return render_template('dashboard.html',params=params, posts=posts)

    if request.method=='POST':
        #REDIRECT TO ADMIN PANEL
        username =  request.form.get('uname')
        userpass = request.form.get('pass')
        if(username==params['admin_user'] and userpass == params['admin_password']):
            #set session variable
            session['user'] = username
            posts = Posts.query.all()
            return  render_template('dashboard.html', params=params, posts=posts)
        else:
            return render_template('login.html', params=params)

    else:
        return render_template('login.html', params=params)

@app.route("/edit/<string:srno>", methods=['GET', 'POST'])
def edit(srno):
    if 'user' in session and session['user'] == params['admin_user']:
        if request.method=='POST':
            box_title = request.form.get('title')
            tline = request.form.get('tline')
            slug = request.form.get('slug')
            content = request.form.get('content')
            img_file = request.form.get('img_file')
            date = datetime.now()
            if srno == '0':
                post = Posts(title=box_title, slug=slug, content=content, tagline=tline, img_file=img_file, date=date)
                db.session.add(post)
                db.session.commit()

            else:
                post = Posts.query.filter_by(srno=srno).first()
                post.title=box_title
                post.slug=slug
                post.content =content
                post.tagline=tline
                post.img_file= img_file
                post.date = date
                # db.session.add(post)
                db.session.commit()
                return redirect('/edit/'+ srno)

        post = Posts.query.filter_by(srno=srno).first()
        return render_template('edit.html', params=params,post=post, srno=srno)

@app.route("/contact", methods = ['GET', 'POST'])
def contact():
    if(request.method=='POST'):
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        entry = Contacts(name=name, phone_num = phone, msg = message, date= datetime.now(),email = email )
        db.session.add(entry)
        db.session.commit()
        mail.send_message('New message from ' + name,
                          sender=email,
                          recipients = [params['gmail-user']],
                          body = message + "\n" + phone
                          )
    return render_template('contact.html', params=params)

@app.route("/uploader", methods=['GET','POST'])
def uploader():
    if request.method=='POST':
        f= request.files['files1']
        f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
        return "Uploaded successfully"

@app.route("/logout")
def logout():
    session.pop('user')
    return redirect('/dashboard')

@app.route("/delete/<string:srno>", methods=['GET', 'POST'])
def delete(srno):
    if 'user' in session and session['user'] == params['admin_user']:
        post=Posts.query.filter_by(srno=srno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/dashboard')

app.run(debug=True)
