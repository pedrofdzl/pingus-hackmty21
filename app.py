from flask import Flask, render_template, redirect, flash, url_for, request
from datetime import datetime

# DB dependencies
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy.orm import backref


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pingus.db'
app.config['SECRET_KEY'] = 'MySuperSecretKey'

# DB
db = SQLAlchemy(app)
migrate = Migrate(app, db)

@app.route('/')
def index():
    return render_template('index.html')

# Log In
from flask_login import (
                        UserMixin, login_manager, login_user, LoginManager,
                        login_required, logout_user, current_user,
)

# Clases camelCase
class Class(db.Model):
    id = db.Column(db.Integer, nullable=False, primary_key=True)
    name = db.Column(db.String, nullable=False)
    quizes = db.relationship('Quiz', backref='Quiz', lazy=True)
    activities = db.relationship('Activity', backref='Activity', lazy=True)
    forum = db.relationship('Forum', backref='Forum', uselist=False)
    lectures = db.relationship('Lecture', backref='Lecture', lazy='True')
    projects = db.relationship('Project', backref='Project', lazy=True)

# todo lo demas snake_case




# Custom Error Pages
@app.errorhandler(404)
def error_404_handler(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def error_500_handler(e):
    return render_template('500.html'), 500


if __name__ == '__main__':
    app.run(debug=True)
