from flask import Flask, render_template, redirect, flash, url_for, request
from datetime import datetime

# DB dependencies
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy.orm import backref
from sqlalchemy.ext.mutable import MutableList

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
