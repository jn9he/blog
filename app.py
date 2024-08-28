from flask import Flask, render_template, session, request, flash
from flask_sqlalchemy import *
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import random, string

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///students.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

app.secret_key = 'super_secret_3'


@app.route('/')
def index():
    if 'username' in session:
        return render_template('dashboard.html')
    else:
        return render_template('login.html')

@app.route('/homepage')
def homepage():
    return render_template('homepage.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return render_template('login.html')
    return render_template('dashboard.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    err = None
    if 'username' in session:
            flash('User already logged in.')
            return render_template('dashboard.html')
    
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user is None:
            err = 'User does not exist.'
            return render_template('login.html', error=err)
        
        elif check_password_hash(user.passHash, request.form['password']):
            session['username'] = request.form['username']
            user.onlineStatus = True
            db.session.commit()
            flash('Welcome' + session['username'])
            return render_template('dashboard.html')
        
        elif not check_password_hash(user.passHash, request.form['password']):
            err = "Incorrect password."
            return render_template('login.html', error=err)
    return render_template('login.html', error=err)

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    if 'username' in session:
        user = User.query.filter_by(username=session['username']).first()
        if user:
            user.onlineStatus = False
    db.session.commit()
    session.clear()
    return render_template('login.html')
    
@app.route('/createUser')
def createUser():
    if 'username' in session:
        return render_template('dashboard.html')
    return render_template('createUser.html')

@app.route('/deleteUser')
def deleteUser(name):
    tbd = User.query.filter_by(username=name).first()
    if tbd is None:
        flash('User does not exist')
        return render_template('homepage.html')
    db.session.delete(tbd)
    db.session.commit()
    flash('User successfully deleted')
    return render_template('homepage.html')

@app.route('/addUser', methods = ['GET', 'POST'])
def addUser():
    msg = None
    if request.method == 'POST':
        if request.form['password'] != request.form['confirmp']:
            flash('Passwords Do Not Match')
            return render_template('createUser.html', message=msg)
        else:
            try:
                user = request.form['username']
                pw = generate_password_hash(request.form['password'])
                new = User(username=user, passHash=pw)

                test_code=generate_user_code()
                while not validate_user_code(test_code):
                    test_code=generate_user_code()
                new.user_code=test_code
                db.session.add(new)
                db.session.commit()

                return render_template('login.html', error="Account created successfully.")
            except IntegrityError:
                db.session.rollback()
                msg = "User already exists."
                return render_template('createUser.html', message=msg)
            
@app.route('/listUsers')
def listUsers():
    users = User.query.all()
    if users is None:
        flash('There are no users registered.')
        return render_template('homepage.html')
    else:
        return render_template('listUsers.html', users=users)
    
@app.route('/createPost')
def createPost():
    prevPosts=None
    if 'username' in session:
        prevPosts=User.query.filter_by(username=session['username'])
        return render_template('createPost.html', posts=prevPosts)
    flash('Please log in first.')
    return render_template('homepage.html')

@app.route('/deletePost')
def deletePost():
    return

@app.route('/viewPost/<int:post_id>', methods=['GET', 'POST'])
def viewPost(post_id):
    thisPost = Post.query.filter_by(id=post_id).first()
    if thisPost is None:
        return render_template('homepage.html', message="Post does not exist.")
    return render_template('viewPost.html', post=thisPost)

@app.route('/addPost', methods=['GET', 'POST'])
def addPost():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        testID = User.query.filter_by(username=session['username']).first().id
        newPost = Post(title=title, content=content, user_id=testID)
        db.session.add(newPost)
        db.session.commit()
        flash('Post Added')
        return render_template('homepage.html')

@app.route('/addComment/<int:postID>', methods=['GET', 'POST'])
def addComment(postID):
    thisPost=Post.query.filter_by(id=postID).first()
    if request.method == 'POST':
        content = request.form['content']
        newComment=Comment(content=content, post_id=postID)
        db.session.add(newComment)
        db.session.commit()

        return render_template('viewPost.html', post=thisPost)

@app.route('/listPosts')
def listPosts(user=None):
    posts = Post.query.all()
    if user is not None:
        posts = Post.query.filter_by(username=user).all()
    if posts is None:
        flash('There are no posts.')
        return render_template('homepage.html')
    else:
        return render_template('listPosts.html', posts=posts)

@app.route('/profile/<string:username>', methods=['GET', 'POST'])
def profile(username):
    user = User.query.filter_by(username=username).first()
    if not user:
        return render_template('homepage.html')
    return render_template('profile.html', posts=Post.query.filter_by(user_id=user.id))

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(25), unique=True, nullable=False)
    passHash = db.Column(db.String, nullable=False)
    onlineStatus = db.Column(db.Boolean, default=False)
    user_code = db.Column(db.String, unique=True, default=None)
    posts = db.relationship('Post', backref='user')

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dt = db.Column(db.DateTime, nullable = False, default=datetime.now)
    title = db.Column(db.String(100))
    content = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    comments = db.relationship('Comment', backref='post')

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dt = db.Column(db.DateTime, nullable=False, default=datetime.now)
    content = db.Column(db.String(150), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)

# class FriendsList(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     userID = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
#     friend_obj = db.Column(db.User)
    

def generate_user_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def validate_user_code(testCode):
    checkUser = User.query.filter_by(user_code=testCode).first()
    if not checkUser:
        return True
    return False


if __name__ == "__Main__":
    app.start(debug=True)