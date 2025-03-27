from flask_login import UserMixin
from .database import db
from datetime import datetime as dt

#should i give the number limitations? no need
    
class User(UserMixin,db.Model):
    id = db.Column(db.Integer,primary_key= True)
    username = db.Column(db.String(),nullable=False,unique=True)
    user_role = db.Column(db.Integer,nullable=False)
    student = db.relationship('Student',backref='user') #u in capital r8? NO
    
    
    def get_id(self):
        return str(self.id)



class Admin(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    passwd = db.Column(db.String(100), nullable=False)

    @property
    def is_admin(self):
        return True  # ✅ Explicitly define admin check


#Why not using usermixin anymore?
class Student(db.Model):  #1
    
    id = db.Column(db.Integer,primary_key= True)
    username = db.Column(db.String(50),nullable=False,unique=True)
    passwd=db.Column(db.String(8),nullable=False,unique=True)
    fullname=db.Column(db.String(30),nullable=False)
    qualification=db.Column(db.String(),nullable=False)
    
    #Integer or string? Date format
    dob = db.Column(db.Date(),nullable=False)
    student_id = db.Column(db.Integer,db.ForeignKey('user.id'),nullable = False)
    


class Subject(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(20),nullable=False,unique=True)
    descrip = db.Column(db.String(100),nullable=False)
    



#Chapter: Each subject can be subdivided into multiple modules called chapters. The possible fields of a chapter can be the following:

#id - primary key
#Name
#Description
#etc: Additional fields (if any)

class Chapter(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(20),nullable=False,unique=True)
    descrip = db.Column(db.String(100))
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)

    subject = db.relationship("Subject", backref="chapters")


#Quiz: A quiz is a test that is used to evaluate the user’s understanding of any particular chapter of any particular subject. A test may contain the following attributes:


#id - primary key
#chapter_id (foreign key-chapter)
#date_of_quiz
#time_duration(hh:mm)
#remarks (if any)
#etc: Additional fields (if any)

class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    chapter_id = db.Column(db.Integer, db.ForeignKey("chapter.id"), nullable=False)
    remarks = db.Column(db.String(100))
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)

    questions = db.relationship("Questions", backref="quiz", lazy=True)
    chapter = db.relationship("Chapter", backref="quizzes", lazy=True)



#Questions: Every quiz will have a set of questions created by the admin. Possible fields for a question include:

#id - primary key
#quiz_id (foreign key-quiz)
#question_statement
#Option1, option2, … etc.
#etc: Additional fields (if any)


class Questions(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    quiz_id = db.Column(db.Integer,db.ForeignKey("quiz.id"),nullable=False)
    question_statement = db.Column(db.String(),nullable=False)
    option1 = db.Column(db.String(),nullable=False)
    option2 = db.Column(db.String(),nullable=False)
    option3 = db.Column(db.String(),nullable=False)
    option4 = db.Column(db.String(),nullable=False)
    correct_option = db.Column(db.String(), nullable=False)

   
#Scores: Stores the scores and details of a user's quiz attempt. Possible fields for scores include:

#id - primary key
#quiz_id (foreign key-quiz)
#user_id (foreign key-user)
#time_stamp_of_attempt
#total_scored
#etc: Additional fields (if any)

class Scores(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey("quiz.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    time_stamp_of_attempt = db.Column(db.DateTime, nullable=False)  
    total_scored = db.Column(db.Integer, nullable=False)

    
    quiz = db.relationship("Quiz", backref=db.backref("scores", lazy=True))



    






