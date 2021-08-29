from flask import Flask, render_template, redirect, flash, url_for, request
from datetime import datetime

# DB dependencies
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# WHAT THE FORMS!!!
from flask_wtf import FlaskForm
from sqlalchemy.ext.declarative import declarative_base
from wtforms import StringField, SubmitField, PasswordField, DateTimeField, BooleanField
from wtforms.validators import DataRequired, EqualTo


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
app.config['SECRET_KEY'] = 'MySuperSecretKey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pingus.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# DB
db = SQLAlchemy(app)
migrate = Migrate(app, db)
Base = declarative_base()

db.create_all()
db.session.commit()

# Clases camelCase

users = db.Table('users',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('class_id', db.ForeignKey('class.id'))
)

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    classes = db.relationship('Class', secondary=users, backref=db.backref('users', lazy='dynamic'))
    username = db.Column(db.String(255), unique=True, nullable=False)
    firstName = db.Column(db.String(255), nullable=False)
    lastName = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    passwordHash = db.Column(db.String(255), nullable=False)
    score = db.Column(db.Integer, default=0)
    isTeacher = db.Column(db.Boolean, default=False)
    dateJoined = db.Column(db.DateTime)
    blogPost_id = db.Column(db.Integer, db.ForeignKey('blogpost.id'))
    notification_id = db.Column(db.Integer, db.ForeignKey('notification.id'))

    @property
    def password(self):
        raise AttributeError('Password is not a readable atribute')

    @password.setter
    def password(self, password):
        self.passwordHash = generate_password_hash(password)


    def verify_password(self, password):        
        return check_password_hash(self.passwordHash, password)


    def __repr__(self) -> str:
        return f'Class:User<{self.username}>'

    def __str__(self) -> str:
        return self.username

# Login Stuff
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'welcome'
login_manager.login_message = 'Please Login to access'

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

class Class(db.Model):
    __tablename__ = 'class'
    id = db.Column(db.Integer, nullable=False, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    quizes = db.relationship('Quiz', backref='owner_class')
    assignments = db.relationship('Assignment', backref='owner_class')
    forum = db.relationship('Forum', backref='owner_class')
    lectures = db.relationship('Lecture', backref='owner_class')

    def __repr__(self):
        return 'Class ' + str(self.id) 

class Quiz(db.Model):
    id = db.Column(db.Integer, nullable=False, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.today)
    questions = db.relationship('Question', backref='owner_quiz')
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'))

    def __repr__(self):
        return 'Quiz ' + str(self.id) 

class Assignment(db.Model):
    id = db.Column(db.Integer, nullable=False, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    datePublished = db.Column(db.DateTime, nullable=False, default=datetime.today)
    dateDue = db.Column(db.DateTime, nullable=False, default=datetime.today)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'))

    def __repr__(self):
        return 'Activity ' + str(self.id) 

class Lecture(db.Model):
    id = db.Column(db.Integer, nullable=False, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.today)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'))

    def __repr__(self):
        return 'Lecture ' + str(self.id) 

class Forum(db.Model):
    id = db.Column(db.Integer, nullable=False, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    blogPosts = db.relationship('BlogPost', backref='owner_forum')
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'))

    def __repr__(self):
        return 'Forum ' + str(self.id) 

class BlogPost(db.Model):
    __tablename__ = 'blogpost'
    id = db.Column(db.Integer, nullable=False, primary_key=True)
    title = db.Column(db.String(255))
    content = db.Column(db.Text, nullable=False)
    user = db.relationship('User', backref='owner_blogpost')
    date = db.Column(db.DateTime, nullable=False, default=datetime.today)
    forum_id = db.Column(db.Integer, db.ForeignKey('forum.id'))

    def __repr__(self):
        return 'BlogPost ' + str(self.id) 

class Question(db.Model):
    id = db.Column(db.Integer, nullable=False, primary_key=True)
    content = db.Column(db.String(255), nullable=False)
    weight = db.Column(db.Float, nullable=False)
    answers = db.relationship('Answer', backref='owner_question')
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'))

class Notification(db.Model):
    id = db.Column(db.Integer, nullable=False, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.today)
    subject = db.Column(db.String(255), nullable=False)
    receivers = db.relationship('User', backref='owner_notification')

    def __repr__(self):
        return 'Notification ' + str(self.id) 

class Answer(db.Model):
    id = db.Column(db.Integer, nullable=False, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'))

    def __repr__(self):
        return 'Answer ' + str(self.id) 


###############
### Forms ####
#############

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(),])
    password = PasswordField('Password', validators=[DataRequired(),])
    submit = SubmitField('Log In!')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(),])
    firstName = StringField('First name', validators=[DataRequired(),])
    lastName = StringField('Last name', validators=[DataRequired(),])
    email = StringField('Email', validators=[DataRequired(),])
    password = PasswordField('Password', validators=[DataRequired(),])
    confirmPassword = PasswordField('Confirm Password', validators=[EqualTo("password"),])
    isTeacher = BooleanField('Teacher')
    submit = SubmitField('Create account')



class QuizForm(FlaskForm):
    name = StringField('Quiz Name', validators=[DataRequired(),])
    description = StringField('Description', validators=[DataRequired(),])
    date = DateTimeField('Date', validators=[DataRequired(),])



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
    form = LoginForm()
    # print('hello')
    if request.method == 'POST' and form.validate():
        user = User.query.filter_by(username=form.username.data).first()
        # print('found')
        
        if user:
            if user.verify_password(form.password.data):
                login_user(user)
                flash(f'Welcome back {user.firstName}!')
                return redirect(url_for('dashboard'))
            else:
                flash('Something went wrong')
        else:
            flash('Something went wrong')

    return render_template('welcome.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    if request.method == 'POST' and form.validate():
        user = User(username = form.username.data, firstName = form.firstName.data, lastName = form.lastName.data, email = form.email.data, isTeacher = form.isTeacher.data, dateJoined = datetime.today())
        user.password = form.password.data
        try:
            db.session.add(user)
            db.session.commit()
            return redirect(url_for('welcome'))
        except:
            flash("Something went wrong")
    return render_template('register.html', form = form)

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


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You\'ve logout')

    return redirect(url_for('index'))


# Custom Error Pages
@app.errorhandler(404)
def error_404_handler(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def error_500_handler(e):
    return render_template('500.html'), 500


if __name__ == '__main__':
    app.run(debug=True)
