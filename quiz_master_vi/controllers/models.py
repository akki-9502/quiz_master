from .database import db
class User(db.Model):
    __tablename__= 'user'
    uid=db.Column(db.Integer,autoincrement=True,primary_key=True,nullable=False)
    username=db.Column(db.String,nullable=False) 
    fullname=db.Column(db.String,nullable=False) 
    dob=db.Column(db.String,nullable=False) 
    qualification=db.Column(db.String,nullable=False) 
    password=db.Column(db.String,nullable=False) 
class File(db.Model):
    __tablename__= 'File'
    uid=db.Column(db.Integer,autoincrement=True,primary_key=True,nullable=False)
    file_url=db.Column(db.String,nullable=False) 
class Admin(db.Model):
    __tablename__= 'admin'
    username=db.Column(db.String,primary_key=True)
    password=db.Column(db.String,nullable=False)
class Subjects(db.Model):
    __tablename__= 'subjects'
    subject_id=db.Column(db.Integer,primary_key=True,autoincrement=True)
    subject_name=db.Column(db.String,nullable=False)
    description=db.Column(db.String,nullable=False)
    chapters = db.relationship('Chapters', backref='subject', lazy=True)

class Chapters(db.Model):
    __tablename__= 'chapters'
    chaoter_id=db.Column(db.Integer,primary_key=True,autoincrement=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.subject_id'), nullable=False)
    chapter_name=db.Column(db.String,nullable=False)
    description=db.Column(db.String,nullable=False)
    questions = db.relationship('Questions', backref='chapter', lazy=True)
    quizzes = db.relationship('QuizDetails', backref='chapter', lazy=True)

class Questions(db.Model):
    __tablename__= 'questions'
    qid = db.Column(db.Integer, primary_key=True, autoincrement=True) 
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapters.chaoter_id'), nullable=False) 
    question = db.Column(db.Text, nullable=False) 
    answer = db.Column(db.Integer, nullable=True) 
    options = db.relationship('Options', backref='question', lazy=True, cascade="all, delete, delete-orphan")
class Options(db.Model):
    __tablename__ = 'options'
    option_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    option = db.Column(db.String, nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.qid',ondelete='CASCADE'), nullable=False)
class QuizDetails(db.Model):
    __tablename__='quiz_details'
    quizid=db.Column(db.Integer,primary_key=True, autoincrement=True)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapters.chaoter_id')) 
    quiz_date=db.Column(db.String,nullable=False)
    duration=db.Column(db.Integer,nullable=False)
class QuizResponse(db.Model):
    __tablename__='quizresponse'
    quizid=db.Column(db.Integer,db.ForeignKey('quiz_details.quizid'),primary_key=True)
    uid=db.Column(db.Integer,db.ForeignKey('user.uid'),primary_key=True)
    questionid=db.Column(db.Integer,db.ForeignKey('questions.qid'),primary_key=True)
    optionid=db.Column(db.Integer,db.ForeignKey('options.option_id'),primary_key=True)
class Scores(db.Model):
    __tablename__= 'scores'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True) 
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz_details.quizid'), nullable=False) 
    uid = db.Column(db.Integer, db.ForeignKey('user.uid'),nullable=False)
    time_stamp = db.Column(db.String, nullable=True) 
    score = db.Column(db.Integer, nullable=True)
    total= db.Column(db.Integer, nullable=True)
    








