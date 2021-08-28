from enum import unique
from flask import Flask, render_template, redirect, flash, url_for, request

# DB dependencies
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

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

# DB
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Login Stuff
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'welcome'


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

###################
#### All routes ##
##################
@app.route('/')
def index():
    if(current_user.is_active):
        return redirect(url_for("dashboard"))
    else:
        return redirect(url_for("welcome"))
    
@app.route('/welcome', methods=['GET', 'POST'])
def welcome():
    username =''
    password = ''

    user = User.query.filter_by(username=username)

    if user:
        if user.verify_password(password):
            login_user(user)
            flash(f'Welcome Back {user.firstName}')


    return render_template('welcome.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/grades')
def grades():
    return render_template('grades.html')
    
@app.route('/classes')
def classes():
    return render_template('classes.html')
    
@app.route('/profile')
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
