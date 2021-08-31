from operator import sub
import re
from typing import Text
from flask import Flask, render_template, redirect, flash, url_for, request, session
from datetime import datetime

# DB dependencies
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, current

# WHAT THE FORMS!!!
from flask_wtf import FlaskForm
from werkzeug.utils import import_string

from wtforms import StringField, SubmitField, PasswordField, BooleanField, IntegerField
from wtforms.fields.core import RadioField, SelectField
from wtforms.validators import DataRequired, EqualTo, ValidationError
from wtforms.widgets import TextArea
from wtforms.ext.dateutil.fields import DateTimeField
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

db.create_all()
db.session.commit()

#imports for jinja
@app.context_processor
def add_imports():
    # Note: we only define the top-level module names!
    return dict(Question=Question, Answer=Answer)

# Clases camelCase

users = db.Table('users',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('class_id', db.ForeignKey('class.id'), primary_key=True)
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
    blogPosts = db.relationship('BlogPost', backref='owner_user', overlaps="blogPosts,owner_user")
    submissions = db.relationship('Submission', backref='owner_user', uselist=True)
    assignments = db.relationship('Assignment', backref='owner_user', uselist=True)
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
    quizzes = db.relationship('Quiz', backref='owner_class')
    assignments = db.relationship('Assignment', backref='owner_class')
    forum = db.relationship('Forum', backref='owner_class', uselist=False)
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
    grade = db.Column(db.Float, nullable=True)

    def __repr__(self):
        return 'Quiz ' + str(self.id) 

class Assignment(db.Model):
    id = db.Column(db.Integer, nullable=False, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    datePublished = db.Column(db.DateTime, nullable=False, default=datetime.today)
    dateDue = db.Column(db.DateTime, nullable=False, default=datetime.today)
    submissions = db.relationship('Submission', backref='owner_assignment', uselist=True)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    submited = db.Column(db.Boolean, default=False)

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
    __tablename__ = 'forum'
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
    date = db.Column(db.DateTime, nullable=False, default=datetime.today)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref='owner_BlogPost', overlaps="blogPosts,owner_user")
    forum_id = db.Column(db.Integer, db.ForeignKey('forum.id'))

    def __repr__(self):
        return 'BlogPost ' + str(self.id) 

class Question(db.Model):
    id = db.Column(db.Integer, nullable=False, primary_key=True)
    content = db.Column(db.String(255), nullable=False)
    weight = db.Column(db.Float, nullable=False, default=0)
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
    isRight = db.Column(db.Boolean, nullable=False, default=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'))

class Submission(db.Model):
    id = db.Column(db.Integer, nullable=False, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    grade = db.Column(db.Integer, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignment.id'))




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


class EditForm(FlaskForm):
    username = StringField('Username', render_kw={'readonly': True})
    firstName = StringField('First name', validators=[DataRequired(),])
    lastName = StringField('Last name', validators=[DataRequired(),])
    email = StringField('Email', render_kw={'readonly': True})
    submit = SubmitField('Save changes')


class ClaseForm(FlaskForm):
    name = StringField('Class name', validators=[DataRequired(message='Name is Required'),])
    submit = SubmitField('Create Class')
    

class QuizForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(),])
    description = StringField('Description', validators=[DataRequired(),], widget=TextArea())
    submit = SubmitField('Submit')


class QuestionForm(FlaskForm):
    content = StringField('Content', validators=[DataRequired(),], widget=TextArea())
    submit = SubmitField('Submit')


class AnswerForm(FlaskForm):
    content = StringField('Content', validators=[DataRequired(),], widget=TextArea())
    isRight = BooleanField('Is this the right answer?')
    submit = SubmitField('Submit')


class AssignmentForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(),])
    description = StringField('Description', validators=[DataRequired(),], widget=TextArea())
    dateDue = DateTimeField('Due Date', validators=[DataRequired(),],)
    submit = SubmitField('Submit')
    

class LectureForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(),])
    content = StringField('Content', validators=[DataRequired(),], widget=TextArea())
    submit = SubmitField('Submit')


class ForumForm(FlaskForm):
    name = StringField('name', validators=[DataRequired(),])
    submit = SubmitField('Submit')


class BlogPostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(),])
    content = StringField('Content', validators=[DataRequired(),], widget=TextArea())
    submit = SubmitField('Submit')


class SubmissionForm(FlaskForm):
    content = StringField('Content', validators=[DataRequired(),], widget=TextArea())
    submit = SubmitField('Submit')


class GradeForm(FlaskForm):
    grade = IntegerField('Grade', description='Value must be between 0-100')
    submit = SubmitField('Submit')

    def validate_grade(self, grade):
        if   0 > grade.data or grade.data > 100:
            flash('Value must be between 0-100')
            raise ValidationError('Value must be between 0-100')

class PreguntaForm(FlaskForm):
    option = SelectField('Option')


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
                #flash(f'Welcome back {user.firstName}!')
                return redirect(url_for('dashboard'))
            else:
                flash('Hooooooly Guacamoooooleeeee... Something went wrong')
        else:
            flash('Hooooooly Guacamoooooleeeee... Something went wrong')

    return render_template('welcome.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
def user_create():
    form = RegisterForm()

    if request.method == 'POST' and form.validate():
        user = User(username = form.username.data, firstName = form.firstName.data, lastName = form.lastName.data, email = form.email.data, isTeacher = form.isTeacher.data, dateJoined = datetime.today())
        user.password = form.password.data
        try:
            db.session.add(user)
            db.session.commit()
            flash('User Registered!')
            return redirect(url_for('welcome'))
        except:
            flash("Something went wrong")
    return render_template('user_create.html', form = form)

@app.route('/edit-profile/<int:id>', methods=['GET', 'POST'])
@login_required
def user_update(id):
    user = User.query.get_or_404(id)
    form = EditForm(request.form, obj=user)

    if request.method == 'POST' and form.validate():
        user.firstName = form.firstName.data
        user.lastName = form.lastName.data
        try:
            db.session.commit()
            return redirect(url_for('profile'))
        except:
            db.session.rollback()
            flash("Something went wrong")
    return render_template('user_update.html', user = user, form = form)

@app.route('/dashboard')
@login_required
def dashboard():
    assignments = current_user.assignments
    submissions = current_user.submissions
    return render_template('dashboard.html', assignments=assignments, submissions=submissions)

@app.route('/grades')
@login_required
def grades():
    submissions = None

    if not current_user.isTeacher:
        submissions = Submission.query.filter_by(user_id=current_user.id).all()

    sum = 0
    c = 0
    if submissions:
        for submission in submissions:
            if submission.grade:
                sum += submission.grade
            c += 1
        if(c > 0):
            gpa = sum / c
    else:
        gpa = 0
    

    return render_template('grades.html', gpa=gpa)
    
@app.route('/classes', methods=['GET', 'POST'])
@login_required
def classes():
    class_list = current_user.classes
    if request.method == 'POST':
        return redirect(url_for('class_create'))
    return render_template('classes.html', lista=class_list)
    
@app.route('/profile')
@login_required
def profile():
    sum = 0
    for submission in current_user.submissions:
        if submission.grade:
            sum += submission.grade
    current_user.score = sum
    try:
        db.session.commit()
    except:
        db.session.rollback()
    return render_template('profile.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You\'ve logged out')
    return redirect(url_for('index'))

@app.route('/delete-account/<int:id>', methods=['GET', 'POST'])
@login_required
def user_delete(id):
    user = User.query.get_or_404(id)
    if request.method == 'POST':
        try:
            db.session.delete(user)
            db.session.commit()
            flash('Your account has been successfully deleted')
            return redirect(url_for('welcome'))
        except:
            db.session.rollback()
            flash("Something went wrong")
    return render_template('user_delete.html', user = user)

@app.route('/classes/register', methods=['GET', 'POST'])
def class_create():
    form = ClaseForm()
    
    if request.method == 'POST' and form.validate():
        clase = Class(name=form.name.data)
        #si hay tiempo extra, validar ultima letra
        forum = Forum(name=f"{clase.name}'s Forum", owner_class=clase)

        try:
            db.session.add(clase)
            clase.users.append(current_user)
            db.session.commit()

            flash('Class Registered Succesfuly!')
            return redirect(url_for('classes'))
        except:
            db.session.rollback()
            flash('Hooooooly Guacamoooooleeeee... Something went wrong')


    return render_template('class_create.html', form=form)

@app.route('/classes/update/<int:id>', methods=['GET', 'POST'])
@login_required
def class_update(id):
    
    clase = Class.query.get_or_404(id)

    form = ClaseForm(request.form, obj=clase)

    if request.method == 'POST' and form.validate():
        clase.name = form.name.data
    
        try:
            db.session.commit()
            flash('Class Updated Succesfully!')
        except:
            db.session.rollback()
            flash('Hooooooly Guacamoooooleeeee... Something went wrong')

    return render_template('class_update.html', form=form)
        

@app.route('/classes/delete/<int:id>', methods=['GET', 'POST'])
@login_required
def class_delete(id):
    clase = Class.query.get_or_404(id)

    try:
        db.session.delete(clase.forum)
        db.session.delete(clase)
        db.session.commit()
        flash('Class Deleted Succesfully!')

    except:
        db.session.rollback()
        flash('Hooooooly Guacamoooooleeeee... Something went wrong')

    return redirect(url_for(''))

@app.route('/classes/detail/<int:id>')
@login_required
def class_detail(id):
    clase = Class.query.get_or_404(id)

    return render_template('class_detail.html', clase=clase)


@app.route('/classes/detail/<int:id>/students')
@login_required
def class_students(id):
    clase = Class.query.get_or_404(id)
    students = clase.users.filter_by(isTeacher=False).all()

    # print(students)

    return render_template('class_students.html', clase=clase, students=students)

@app.route('/classes/detail/<int:id>/students/add-student', methods=['GET', 'POST'])
@login_required
def class_add_student(id):
    clase = Class.query.get_or_404(id)
    students = None

    if request.method == "POST":
        username = request.form['student']
        students = User.query.filter_by(username=username, isTeacher=False).all()
    
    else:
        students = User.query.filter_by(isTeacher=False).all()



    return render_template('class_add_student.html', clase=clase, students=students)

@app.route('/classes/detail/<int:classid>/students/add-student/<int:studid>')
@login_required
def class_add(classid, studid):

    clase = Class.query.get_or_404(classid)
    user = User.query.get_or_404(studid)

    try:
        clase.users.append(user)
        db.session.commit()
        flash('Student Added Succesfully')
    except:
        db.session.rollback()
        flash('Student Already added!')

    return redirect(url_for('class_students', id=clase.id))
    
@app.route('/classes/detail/<int:classid>/students/remove-student/<int:studid>')
@login_required
def class_remove(classid, studid):

    clase = Class.query.get_or_404(classid, studid)
    user = User.query.get_or_404(studid)

    try:
        clase.users.remove(user)
        db.session.commit()
        flash('Student Remove succesfully')
    except:
        db.session.rollback()
        flash('Student not in class')

    return redirect(url_for('class_students', id=clase.id))



# Lectures
@app.route('/classes/detail/<int:classid>/lecture/create', methods=['GET', 'POST'])
@login_required
def lecture_create(classid):

    clase = Class.query.get_or_404(classid)
    form = LectureForm()

    if request.method == 'POST' and form.validate():
        lecture = Lecture(name=form.name.data, content=form.content.data)
        lecture.class_id = clase.id

        try:
            db.session.add(lecture)
            db.session.commit()
            flash('Lecutre Created Succesfully!')
            return redirect(url_for('lecture_detail', classid=clase.id, lectid=lecture.id))
        except:
            flash('Hooooooly Guacamoooooleeeee... Something went wrong')

    return render_template('lecture_create.html', form=form, clase=clase)


@app.route('/classes/detail/<int:classid>/lecture/update/<int:lectid>', methods=['GET', 'POST'])
@login_required
def lecture_update(classid, lectid):

    clase = Class.query.get_or_404(classid)
    lecture = Lecture.query.get_or_404(lectid)

    form = LectureForm(request.form, obj=lecture)

    if request.method == 'POST' and form.validate():
        lecture.name = form.name.data
        lecture.content = form.content.data

        try:
            db.session.commit()
            flash('Lecture Update Succesfuly!')
            return redirect(url_for('lecture_detail', classid=clase.id, lectid=lecture.id))
        except:
            flash('Hooooooly Guacamoooooleeeee... Something went wrong')
    
    return render_template('lecture_update.html', form=form, clase=clase)


@app.route('/classes/detail/<int:classid>/lecture/delete/<int:lectid>')
@login_required
def lecture_delete(classid, lectid):
    clase = Class.query.get_or_404(classid)
    lecture = Lecture.query.get_or_404(lectid)

    try:
        db.session.delete(lecture)
        db.session.commit()
        flash('Lecture Delete Succesfuly!')
        return redirect(url_for('class_detail', id=clase.id))
    except:
        db.session.rollback()
        flash('Hooooooly Guacamoooooleeeee... Something went wrong')

    return redirect(url_for('lecture_detail', classid=clase.id, lectid=lecture.id))


@app.route('/classes/detail/<int:classid>/lecture/detail/<int:lectid>')
@login_required
def lecture_detail(classid, lectid):
    clase = Class.query.get_or_404(classid)
    lecture = Lecture.query.get_or_404(lectid)
    
    return render_template('lecture_detail.html', clase=clase, lecture=lecture)


@app.route('/classes/detail/<int:classid>/assignment/create', methods=['GET', 'POST'])
@login_required
def assignment_create(classid):
    clase = Class.query.get_or_404(classid)
    form = AssignmentForm()

    # print(form.dueDate.data)
    if request.method == 'POST' and form.validate():
        assignment = Assignment(name=form.name.data, description=form.description.data, dateDue=form.dateDue.data)
        students = User.query.filter_by(isTeacher = False).all()
        for student in students:
            for c in student.classes:
                if(c == clase):
                    student.assignments.append(assignment)
        assignment.class_id = clase.id

        try:
            db.session.add(assignment)
            db.session.commit()
            flash('Assignment added succesfully')
            return redirect(url_for('assignment_detail', classid=clase.id, assid=assignment.id))
        except:
            db.session.rollback()
            flash('Hooooooly Guacamoooooleeeee... Something went wrong')
        
    return render_template('assignment_create.html', form=form, clase=clase)


@app.route('/classes/detail/<int:classid>/assignment/update/<int:assid>', methods=['GET', 'POST'])
@login_required
def assignment_update(classid, assid):
    clase = Class.query.get_or_404(classid)
    assignment = Assignment.query.get_or_404(assid)

    form = AssignmentForm(request.form, obj=assignment)

    if request.method == 'POST' and form.validate():
        assignment.name = form.name.data
        assignment.description = form.description.data
        assignment.dateDue = form.dateDue.data
        
        try:
            db.session.commit()
            flash('Assignment Updated Succesfuly!')
            return redirect(url_for('assignment_detail', classid=clase.id, assid=assignment.id))
        except:
            db.session.rollback()
            flash('Hooooooly Guacamoooooleeeee... Something went wrong')
        
    return render_template('assignment_update.html', form=form, clase=clase, assignment=assignment)

@app.route('/classes/detail/<int:classid>/assignment/detail/<int:assid>')
@login_required
def assignment_detail(classid, assid):
    clase = Class.query.get_or_404(classid)
    assignment = Assignment.query.get_or_404(assid)
    submissions = None

    submission = Submission.query.filter_by(user_id=current_user.id, assignment_id=assignment.id).first()

    if current_user.isTeacher:
        submissions = Submission.query.filter_by(assignment_id=assignment.id).all()

    return render_template('assignment_detail.html', clase=clase, assignment=assignment, submission=submission, submissions=submissions, user=User)


@app.route('/classes/detail/<int:classid>/assignment/delete/<int:assid>')
@login_required
def assignment_delete(classid, assid):
    clase = Class.query.get_or_404(classid)
    assignment = Assignment.query.get_or_404(assid)

    try:
        db.session.delete(assignment)
        db.session.commit()
        flash('Assignment deleted Succesfully!')
        return redirect(url_for('class_detail', id=clase.id))
    except:
        db.session.rollback()
        flash('Hooooooly Guacamoooooleeeee... Something went wrong')
    
    return redirect(url_for('assignment_detail', classid=clase.id, assid=assignment.id))



@app.route('/classes/detail/<int:classid>/assignment/detail/<int:assid>/submission', methods=['GET', 'POST'])
@login_required
def submission_upload(classid, assid):
    clase = Class.query.get_or_404(classid)
    assignment = Assignment.query.get_or_404(assid)

    form = SubmissionForm()

    if request.method == 'POST' and form.validate():
        submission = Submission(content=form.content.data)
        submission.user_id = current_user.id
        submission.assignment_id = assignment.id
        assignment.submited = True

        try:
            db.session.add(submission)
            db.session.commit()
            flash('Assignment Uploaded Succesfully')
            return redirect(url_for('assignment_detail', classid=clase.id, assid=assignment.id))
        except:
            db.session.rollback()
            flash('Hooooooly Guacamoooooleeeee... Something went wrong')
        
    return render_template('submission_upload.html', clase=clase, assignment=assignment, form=form)


@app.route('/classes/detail/<int:classid>/assignment/detail/<int:assid>/submission/<int:subid>')
@login_required
def submission_detail(classid, assid, subid):
    clase = Class.query.get_or_404(classid)
    assignment = Assignment.query.get_or_404(assid)
    submission = Submission.query.get_or_404(subid)

    author = User.query.get_or_404(submission.user_id)

    return render_template('submission_detail.html', clase=clase, assignment=assignment, submission=submission, author=author)


@app.route('/classes/detail/<int:classid>/assignment/detail/<int:assid>/submission/<int:subid>/update', methods=['GET', 'POST'])
@login_required
def submission_update(classid, assid, subid):
    clase = Class.query.get_or_404(classid)
    assignment = Assignment.query.get_or_404(assid)
    submission = Submission.query.get_or_404(subid)

    form = SubmissionForm(request.form, obj=submission)

    if request.method == 'POST' and form.validate():
        submission.content = form.content.data

        try:
            db.session.commit()
            flash('Assignment Updated Succesfully')
            return redirect(url_for('assignment_detail', classid=clase.id, assid=assignment.id))
        except:
            db.session.rollback()
            flash('Hooooooly Guacamoooooleeeee... Something went wrong')


    return render_template('submission_update.html', clase=clase, assignment=assignment, submission=submission, form=form)


@app.route('/classes/detail/<int:classid>/assignment/detail/<int:assid>/submission/<int:subid>/delete')
@login_required
def submission_delete(classid, assid, subid):
    clase = Class.query.get_or_404(classid)
    assignment = Assignment.query.get_or_404(assid)
    submission = Submission.query.get_or_404(subid)
    
    
    try:
        db.session.delete(submission)
        db.session.commit()
        flash('Assignment Updated Succesfully')
    except:
        db.session.rollback()
        flash('Hooooooly Guacamoooooleeeee... Something went wrong')

    return redirect(url_for('assignment_detail', classid=clase.id, assid=assignment.id))


@app.route('/classes/detail/<int:classid>/assignment/detail/<int:assid>/submission/<int:subid>/grade', methods=['GET', 'POST'])
@login_required
def submission_grade(classid, assid, subid):
    clase = Class.query.get_or_404(classid)
    assignment = Assignment.query.get_or_404(assid)
    submission = Submission.query.get_or_404(subid)

    form = GradeForm()


    if request.method == 'POST' and form.validate():
        submission.grade = form.grade.data

        try:
            db.session.commit()
            flash('Assignment Graded Succesfully')
            return redirect(url_for('assignment_detail', classid=clase.id, assid=assignment.id))

        except:
            db.session.rollback()
            flash('Hooooooly Guacamoooooleeeee... Something went wrong')
    
    return render_template('submission_grade.html',  clase=clase, assignment=assignment, submission=submission, form=form)


@app.route('/classes/detail/<int:classid>/forum/blogPost/create', methods=['GET','POST'])
@login_required
def blogPost_create(classid):
    clase = Class.query.get_or_404(classid)

    form = BlogPostForm()

    if request.method == 'POST' and form.validate():
        blogPost = BlogPost(title=form.title.data, content=form.content.data)
        blogPost.forum_id = clase.forum.id
        current_user.blogPosts.append(blogPost)

        try:
            db.session.add(blogPost)
            db.session.commit()
            flash('Blog Post Added Succesfully')
            return redirect(url_for('class_detail', id=clase.id))
        except:
            db.session.rollback()
            flash('Hooooooly Guacamoooooleeeee... Something went wrong')
        
    return render_template('blogPost_create.html', form=form, clase=clase)

@app.route('/classes/detail/<int:classid>/forum/blogPost/update/<int:postid>', methods=['GET','POST'])
@login_required
def blogPost_update(classid, postid):
    clase = Class.query.get_or_404(classid)
    blogPost = BlogPost.query.get_or_404(postid)

    form = BlogPostForm(request.form, obj=blogPost)

    if request.method == 'POST' and form.validate():
        blogPost.title = form.title.data
        blogPost.content = form.content.data
        
        try:
            db.session.commit()
            flash('Blog Post Updated Succesfuly!')
            return redirect(url_for('blogPost_detail', classid=clase.id, postid=blogPost.id))
        except:
            db.session.rollback()
            flash('Hooooooly Guacamoooooleeeee... Something went wrong')
        
    return render_template('blogPost_update.html', form=form)

@app.route('/classes/detail/<int:classid>/forum/blogPost/delete/<int:postid>')
@login_required
def blogPost_delete(classid, postid):
    clase = Class.query.get_or_404(classid)
    blogPost = BlogPost.query.get_or_404(postid)

    try:
        db.session.delete(blogPost)
        db.session.commit()
        flash('Blog Post Deleted Succesfuly!')
        return redirect(url_for('class_detail', id=clase.id))
    except:
        db.session.rollback()
        flash('Hooooooly Guacamoooooleeeee... Something went wrong')

    return redirect(url_for('class_detail', id=clase.id))

@app.route('/classes/detail/<int:classid>/forum/blogPost/detail/<int:postid>')
@login_required
def blogPost_detail(classid, postid):
    clase = Class.query.get_or_404(classid)
    blogPost = BlogPost.query.get_or_404(postid)

    return render_template('class_detail.html', clase=clase)

@app.route('/classes/detail/<int:classid>/rankings')
@login_required
def class_rankings(classid):

    clase = Class.query.get_or_404(classid)
    users = clase.users.filter_by(isTeacher = False).order_by(User.score.desc()).all()
    for user in users:
        sum =0 
        for submission in user.submissions:
            if submission.grade:
                sum += submission.grade
        user.score = sum
        try:
            db.session.commit()
        except:
            db.session.rollback()

    return render_template('class_rankings.html', clase=clase, users = users)

@app.route('/classes/detail/<int:classid>/quiz/create', methods=['GET','POST'])
@login_required
def quiz_create(classid):
    clase = Class.query.get_or_404(classid)

    form = QuizForm()

    if request.method == 'POST' and form.validate():
        quiz = Quiz(name=form.name.data, description=form.description.data)
        clase.quizzes.append(quiz)

        try:
            db.session.add(quiz)
            db.session.commit()
            flash('Quiz Added Succesfully')
            return redirect(url_for('question_create', classid=clase.id, quizid=quiz.id))
        except:
            db.session.rollback()
            flash('Hooooooly Guacamoooooleeeee... Something went wrong')
        
    return render_template('quiz_create.html', form=form, clase=clase)

@app.route('/classes/detail/<int:classid>/quiz/detail/<int:quizid>')
@login_required
def quiz_detail(classid, quizid):
    clase = Class.query.get_or_404(classid)
    quiz = Quiz.query.get_or_404(quizid)

    return render_template('quiz_detail.html', clase=clase, quiz=quiz)

@app.route('/classes/detail/<int:classid>/quiz/<int:quizid>/respond', methods=['GET','POST'])
@login_required
def quiz_respond(classid, quizid):
    clase = Class.query.get_or_404(classid)
    quiz = Quiz.query.get_or_404(quizid)
    questions = quiz.questions

    questions_dict = {}
    for question in questions:
        temp_answers = []
        for answer in question.answers:
            temp_answers.append(answer.id)
        questions_dict[question.id] = temp_answers

    correct = 0
    score = 0
    if request.method=='POST':
        for question in questions_dict:
            answered = (request.form.to_dict())
            if Answer.query.get_or_404(answered.get(str(question))).isRight == True:
                correct += 1
                score += Question.query.get_or_404(question).weight
        return render_template('quiz_responded.html', questions=questions_dict, quiz=quiz, correct=correct, answered=answered, score=score)

    return render_template('quiz_respond.html', questions=questions_dict, clase=clase, quiz=quiz)

@app.route('/classes/detail/<int:classid>/quiz/<int:quizid>/question/create', methods=['GET','POST'])
@login_required
def question_create(classid, quizid):
    clase = Class.query.get_or_404(classid)
    quiz = Quiz.query.get_or_404(quizid)
    form = QuestionForm()

    if request.method == 'POST' and form.validate():
        question = Question(content=form.content.data)

        try:
            db.session.add(question)
            quiz.questions.append(question)
            db.session.commit()

            if len(quiz.questions) != 0:
                temp_weight = 100 / len(quiz.questions)
                print(temp_weight)
                for question in quiz.questions: 
                    db.session.delete(question)
                    for answer in question.answers:
                        db.session.add(answer)         
                    question.weight = temp_weight
                    db.session.add(question)
                    db.session.commit()

            else:
                temp_weight = 100
                question.weight = temp_weight

            flash('Question Added Succesfully')
            return redirect(url_for('answer_create', classid=clase.id, questionid=question.id, quizid=quiz.id))

        except:
            db.session.rollback()
            flash('Hooooooly Guacamoooooleeeee... Something went wrong')
        
    return render_template('question_create.html', form=form, clase=clase, quiz=quiz)

@app.route('/classes/detail/<int:classid>/quiz/<int:quizid>/question/<int:questionid>/answer/create', methods=['GET','POST'])
@login_required
def answer_create(classid, questionid, quizid):
    clase = Class.query.get_or_404(classid)
    quiz = Quiz.query.get_or_404(quizid)
    question = Question.query.get_or_404(questionid)
    right_exists = False

    if len(question.answers) == 4:
        return redirect(url_for('quiz_detail', classid=clase.id, quizid=quiz.id))
    form = AnswerForm()
    
    for answer in question.answers:
        if answer.isRight:
            right_exists = True

    if request.method == 'POST' and form.validate():
        answer = Answer(content=form.content.data, isRight=form.isRight.data)
        db.session.add(answer)
        question.answers.append(answer)
        db.session.commit()

        try:
            
            flash('Answer Added Succesfully')
            return redirect(url_for('answer_create', classid=clase.id, questionid=question.id, quizid=quiz.id))
        except:
            db.session.rollback()
            flash('Hooooooly Guacamoooooleeeee... Something went wrong')
        
    return render_template('answer_create.html', form=form, clase=clase, question=question, quiz=quiz, right_exists=right_exists)

# Custom Error Pages
@app.errorhandler(404)
def error_404_handler(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def error_500_handler(e):
    return render_template('500.html'), 500


if __name__ == '__main__':
    app.run(debug=True)
