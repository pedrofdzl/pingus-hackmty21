from enum import unique
from flask import Flask, render_template, redirect, flash, url_for, request
from datetime import datetime

# DB dependencies
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy.orm import backref
from sqlalchemy.ext.mutable import MutableList


# Log In
from flask_login import (
                        UserMixin, login_manager, login_user, LoginManager,
                        login_required, logout_user, current_user,
)

# Manage Passwords
from werkzeug.security import generate_password_hash, check_password_hash
import bcrypt

from random import randint

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pingus.db'
app.config['SECRET_KEY'] = 'MySuperSecretKey'

# DB
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Clases camelCase
# todo lo demas snake_case
class User(db.Model, UserMixin):
    _id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    firstName = db.Column(db.String(255), nullable=False)
    lastName = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    passwordHash = db.Column(db.String(255), nullable=False)
    score = db.Column(db.Integer, default=0)
    isTeacher = db.Column(db.Boolean, default=False)
    dateJoined = db.Column(db.DateTime)

    @property
    def password(self):
        raise AttributeError('Password is not a readable atribute')

    @password.setter
    def password(self, password):
        engine = randint(0,1)

        if engine == 0:
            self.passwordHash = generate_password_hash(password)
        else:
            self.passwordHash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    def verify_password(self, password):
        
        if check_password_hash(self.passwordHash, password):
            return True
        elif bcrypt.checkpw(password.encode('utf-8'), self.passwordHash):
            return True
        
        return False


    def __repr__(self) -> str:
        return f'Class:User<{self.username}>'

    def __str__(self) -> str:
        return self.username

# Login Stuff
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'welcome'

@login_manager.user_loader
def load_user(user):
    return User.query.get(user)

# Clases camelCase
# todo lo demas snake_case
class Class(db.Model):
    __tablename__ = 'parent' 
    id = db.Column(db.Integer, nullable=False, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    quizes = db.relationship('Quiz', backref='Quiz', lazy=True)
    #activities = db.relationship('Activity', backref='Activity', lazy=True)
    #forum = db.relationship('Forum', backref=backref('Forum', uselist='False'))
    #lectures = db.relationship('Lecture', backref='Lecture', lazy=True)
    #projects = db.relationship('Project', backref='Project', lazy=True)

    def __repr__(self):
        return 'Class ' + str(self.id) 

class Quiz(db.Model):
    __tablename__ = 'child'
    id = db.Column(db.Integer, nullable=False, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    #questions = db.relationship('Question', back_populates='Question', lazy=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('parent.id'))

    def __repr__(self):
        return 'Quiz ' + str(self.id) 
'''
class Activity(db.Model):
    __tablename__ = 'child'
    id = db.Column(db.Integer, nullable=False, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=False)
    datePublished = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    dateDue = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    parent_id = db.Column(db.Integer, db.ForeignKey('parent.id'))

    def __repr__(self):
        return 'Activity ' + str(self.id) 

class Lecture(db.Model):
    __tablename__ = 'child'
    id = db.Column(db.Integer, nullable=False, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    content = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    parent_id = db.Column(db.Integer, db.ForeignKey('parent.id'))

    def __repr__(self):
        return 'Lecture ' + str(self.id) 
'''

'''
class Question(db.Model):
    __tablename__ = 'child'
    id = db.Column(db.Integer, nullable=False, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    weight = db.Column(db.Float, nullable=False)
    answers = db.Column(MutableList.as_mutable(db.PickleType), default=[])
    parent_id = db.Column(db.Integer, db.ForeignKey('parent.id'))

    def __repr__(self):
        return 'Question ' + str(self.id) 

'''

###################
#### All routes ##
##################
@app.route('/')
def index():
    if(current_user.is_authenticated):
        return redirect(url_for("dashboard"))
    else:
        return redirect(url_for("welcome"))

    
@app.route('/welcome', methods=['GET', 'POST'])
def welcome():
    # username =''
    # password = ''
    # user = User.query.filter_by(username=username)

    # if user:
    #     if user.verify_password(password):
    #         login_user(user)
    #         flash(f'Welcome Back {user.firstName}')
    return render_template('welcome.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/grades')
@login_required
def grades():
    return render_template('grades.html')
    
@app.route('/classes')
@login_required
def classes():
    return render_template('classes.html')
    
@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')



# Custom Error Pages
@app.errorhandler(404)
def error_404_handler(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def error_500_handler(e):
    return render_template('500.html'), 500


if __name__ == '__main__':
    app.run(debug=True)
