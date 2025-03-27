import os
import time
from flask import Flask, render_template, redirect, request, url_for, session, flash, abort
from flask_login import login_required, current_user, login_user, logout_user,login_manager
from collections import Counter
from app import app
from sqlalchemy.orm import joinedload
from datetime import datetime,date
from .models import *

import matplotlib  # type: ignore
import matplotlib.ticker as ticker # type: ignore
import matplotlib.pyplot as plt # type: ignore
matplotlib.use("Agg")


def quiz_is_active(start_date, end_date):
    """Check if the quiz is active based on the current date."""
    present_date = date.today()
    return start_date <= present_date < end_date


#________________ADMIN LOGIN_______________#

@app.route('/admin_dashboard')
@login_required
def admin_dashboard():
    subjects = Subject.query.all()
    return render_template("admin_dash.html",subjects=subjects,u_name=current_user.username)  # Make sure this template exists


@app.route('/adminlogin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        u_name = request.form.get("u_name")
        pwd = request.form.get("pwd")
        this_admin = Admin.query.filter_by(username=u_name).first()

        if not this_admin:
            print("DEBUG: No admin found with username:", u_name)
            return render_template("admin_login.html", error="Admin does not exist")
        
        if this_admin.passwd != pwd:
            print("DEBUG: Incorrect password for admin:", u_name)
            return render_template('admin_login.html', error="Incorrect password.")

        print("DEBUG: Admin found ->", this_admin)
        login_user(this_admin, remember=True)  # ✅ Admin is logged in
        
        session['admin_logged_in'] = True  # ✅ Ensure session persists
        print("DEBUG: Logged in as Admin:", current_user)

        return redirect(url_for('admin_dashboard'))

    return render_template('admin_login.html')



#____________________ADMIN LOGOUT____________________________#
@app.route('/admin_logout')
@login_required
def admin_logout():
    logout_user()
    return render_template('admin_login.html')


        




#--------------STUDENT--------------#
#student logout#

@app.route('/student_logout')
@login_required
def student_logout():
    logout_user()
    return render_template("student_login.html")

#------------STUDENT REGISTRATION----------------#

@app.route('/studentregister',methods=['GET','POST'])
def stud_reg():
    if request.method == "POST":
        
        u_name = request.form.get("u_name")
        pwd= request.form.get("pwd")
        flname = request.form.get("flname")
        qual = request.form.get("qual")

        dobirth = request.form.get("dobirth")
        dobirth = datetime.strptime(dobirth, '%Y-%m-%d').date()
        if not (u_name and pwd and flname and qual and dobirth):
            return render_template('student_register.html',message = 'Student Details not complete,please try again.')
    
        this_student = Student.query.filter_by(username = u_name).first()
        if this_student:
            return "Student already exists"
        else:
            new_user = User(username = u_name,user_role=1)
            db.session.add(new_user)
            db.session.commit()
            new_student = Student(username = u_name, passwd = pwd, fullname = flname , qualification = qual , dob = dobirth, student_id = new_user.id)
            db.session.add(new_student)
            db.session.commit()
            return redirect('/studentlogin')
    return render_template('student_register.html')

#------------STUDENT LOGIN-----------

@app.route('/studentlogin',methods = ['GET','POST'])
def stud_login():
    if request.method == 'POST':
        
        u_name = request.form.get("u_name")
        pwd= request.form.get("pwd")
        this_student = User.query.filter_by(username = u_name).first() # why filtering from user table and not student table, can login only when previously registered r8?,so details should be in student table
        if not this_student:
            return render_template('student_login.html',error='Student does not exist.')
        if not Student.query.filter_by(student_id=this_student.id,passwd=pwd).first():
            return render_template('student_login.html',error='Incorrect password.')
        
       
        if this_student.user_role == 1:
            login_user(this_student)
            return redirect(url_for('user_dashboard'))
    return render_template('student_login.html')


#_______________STUDENT DASHBOARD_____________#




@app.route('/dashboard', methods=['GET'])
@login_required
def user_dashboard():
    today = date.today()
    search_query = request.args.get('search', '').strip()

    quizzes = Quiz.query.join(Chapter).join(Subject).filter(Quiz.start_date >= today)


    if search_query:
        # Ensure filtering through the correct relationships
        quizzes = quizzes.filter(
            (Quiz.name.ilike(f"%{search_query}%")) |
            (Chapter.name.ilike(f"%{search_query}%")) |
            (Subject.name.ilike(f"%{search_query}%"))
        )

    quizzes = quizzes.options(
        joinedload(Quiz.chapter).joinedload(Chapter.subject)
    ).all()

    quiz_data = [
        {
            'id': quiz.id,
            'name': quiz.name,
            'num_questions': Questions.query.filter_by(quiz_id=quiz.id).count(),
            'date': quiz.start_date.strftime('%d/%m/%Y')
        }
        for quiz in quizzes
    ]

    return render_template('user_dashboard.html', user=current_user, quizzes=quiz_data, search_query=search_query)


# ____________ CREATE SUBJECT ______________ #
@app.route('/create_subject', methods=['POST'])
@login_required  
def create_subject():
    print(f"Current user: {current_user}, Type: {type(current_user)}")  # Debugging line
    
    if not getattr(current_user, 'is_admin', False):  # ✅ This works

        print("User is NOT an admin!")  # Debugging line
        return "Unauthorized", 403  

    name = request.form.get("name")
    desc = request.form.get("desc")

    if not name or not desc:
        return redirect(url_for('admin_dashboard'))

    existing_subject = Subject.query.filter_by(name=name).first()
    if existing_subject:
        return "Subject with this name already exists!", 400

    new_subject = Subject(name=name, descrip=desc)
    db.session.add(new_subject)
    db.session.commit()

    return redirect(url_for('admin_dashboard'))

@app.route('/update_subject/<int:subject_id>', methods=['POST'])
@login_required
def update_subject(subject_id):
    subject = Subject.query.get(subject_id)
    if subject:
        new_name = request.form.get('name')
        new_desc = request.form.get('desc')
        if new_name:
            subject.name = new_name
        if new_desc:
            subject.descrip = new_desc
        db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/delete_subject/<int:subject_id>', methods=['POST'])
@login_required
def delete_subject(subject_id):
    """ Delete a subject along with its chapters, quizzes, and questions """
    subject = Subject.query.get_or_404(subject_id)  # Ensure subject exists

    # Step 1: Delete all questions under quizzes in this subject
    for chapter in subject.chapters:
        for quiz in chapter.quizzes:
            Questions.query.filter_by(quiz_id=quiz.id).delete()  # Delete questions

    # Step 2: Delete all quizzes under chapters of this subject
    for chapter in subject.chapters:
        Quiz.query.filter_by(chapter_id=chapter.id).delete()  # Delete quizzes

    # Step 3: Delete all chapters under this subject
    Chapter.query.filter_by(subject_id=subject.id).delete()  # Delete chapters

    # Step 4: Finally, delete the subject itself
    db.session.delete(subject)
    db.session.commit()

    return redirect(url_for('admin_dashboard'))


#______---CHAPTERS_______________-#

# ____________ CHAPTERS CRUD ROUTES ______________ #

@app.route('/chapters/<int:subject_id>')
@login_required
def view_chapters(subject_id):
    """ View all chapters for a given subject """
    subject = Subject.query.get_or_404(subject_id)
    chapters = Chapter.query.filter_by(subject_id=subject_id).all()
    return render_template("chapters.html", subject=subject, chapters=chapters)


@app.route('/add_chapter/<int:subject_id>', methods=['POST'])
@login_required
def add_chapter(subject_id):
    """ Add a new chapter under a subject """
    name = request.form.get("name")
    descrip = request.form.get("description")

    if not name or not descrip:
        return redirect(url_for('view_chapters', subject_id=subject_id))

    new_chapter = Chapter(name=name, descrip=descrip, subject_id=subject_id)
    db.session.add(new_chapter)
    print(new_chapter.descrip)
    db.session.commit()

    return redirect(url_for('view_chapters', subject_id=subject_id))


@app.route('/update_chapter/<int:chapter_id>', methods=['POST'])
@login_required
def update_chapter(chapter_id):
    """ Update an existing chapter """
    chapter = Chapter.query.get_or_404(chapter_id)
    new_name = request.form.get('name')
    new_description = request.form.get('description')

    if new_name:
        chapter.name = new_name
    if new_description:
        chapter.descrip = new_description

    db.session.commit()
    return redirect(url_for('view_chapters', subject_id=chapter.subject_id))


@app.route('/delete_chapter/<int:chapter_id>', methods=['POST'])
@login_required
def delete_chapter(chapter_id):
    """ Delete a chapter """
    chapter = Chapter.query.get(chapter_id)#is it necessary to give get_or_404
    subject_id = chapter.subject_id
    
    for quiz in chapter.quizzes:
        Questions.query.filter_by(quiz_id=quiz.id).delete()  # Delete questions

    # Then, delete all quizzes under this chapter
    Quiz.query.filter_by(chapter_id=chapter.id).delete()
    
    db.session.delete(chapter)
    db.session.commit()
    
    return redirect(url_for('view_chapters', subject_id=subject_id))



# ____________ QUIZZES CRUD ROUTES ______________ #

@app.route('/quizzes/<int:chapter_id>')
@login_required
def view_quizzes(chapter_id):
    
    chapter = Chapter.query.get_or_404(chapter_id)
    quizzes = Quiz.query.filter_by(chapter_id=chapter_id).all()

   
    for quiz in quizzes:
        quiz.is_active = quiz_is_active(quiz.start_date, quiz.end_date)

    return render_template("quizzes.html", chapter=chapter, quizzes=quizzes)



@app.route('/add_quiz/<int:chapter_id>', methods=['POST'])
@login_required
def add_quiz(chapter_id):
    
    name = request.form.get("name")
    remarks = request.form.get("remarks")
    start_date_str = request.form.get("start_date")
    end_date_str = request.form.get("end_date")

    if not name or not remarks or not start_date_str or not end_date_str:
        return redirect(url_for('view_quizzes', chapter_id=chapter_id))

    
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

    new_quiz = Quiz(name=name , remarks=remarks, start_date=start_date, end_date=end_date, chapter_id=chapter_id)
    db.session.add(new_quiz)
    db.session.commit()

    return redirect(url_for('view_quizzes', chapter_id=chapter_id))

@app.route('/update_quiz/<int:quiz_id>', methods=['POST'])
@login_required
def update_quiz(quiz_id):
    """ Update an existing quiz """
    quiz = Quiz.query.get_or_404(quiz_id)
    
    new_remarks = request.form.get('remarks')
    new_start_date_str = request.form.get('start_date')
    new_end_date_str = request.form.get('end_date')

    if new_remarks:
        quiz.remarks = new_remarks
    if new_start_date_str:
        quiz.start_date = datetime.strptime(new_start_date_str, '%Y-%m-%d').date()
    if new_end_date_str:
        quiz.end_date = datetime.strptime(new_end_date_str, '%Y-%m-%d').date()

    db.session.commit()
    return redirect(url_for('view_quizzes', chapter_id=quiz.chapter_id))


@app.route('/delete_quiz/<int:quiz_id>', methods=['POST'])
@login_required
def delete_quiz(quiz_id):
    """ Delete a quiz """
    quiz = Quiz.query.get(quiz_id)
    chapter_id = quiz.chapter_id

    Questions.query.filter_by(quiz_id=quiz.id).delete()

    db.session.delete(quiz)
    db.session.commit()
    
    return redirect(url_for('view_quizzes', chapter_id=chapter_id))





# ____________ QUESTIONS CRUD ROUTES ______________ #

@app.route('/questions/<int:quiz_id>')
@login_required
def view_questions(quiz_id):
    """ View all questions for a given quiz """
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = Questions.query.filter_by(quiz_id=quiz_id).all()

    print("Retrieved Questions:", questions)  # Debugging line

    return render_template("questions.html", quiz=quiz, questions=questions)

@app.route('/add_question/<int:quiz_id>', methods=['POST'])
@login_required
def add_question(quiz_id):
    """ Add a new question under a quiz """
    question_statement = request.form.get("question_statement")  # Change 'text' to 'question_statement'
    option_a = request.form.get("option_a")
    option_b = request.form.get("option_b")
    option_c = request.form.get("option_c")
    option_d = request.form.get("option_d")
    correct_option = request.form.get("correct_option")

    if not question_statement or not option_a or not option_b or not option_c or not option_d or not correct_option:
        return redirect(url_for('view_questions', quiz_id=quiz_id))

    new_question = Questions(
        question_statement=question_statement,  # Use correct column name
        option1=option_a, 
        option2=option_b, 
        option3=option_c, 
        option4=option_d, 
        correct_option = correct_option,
        quiz_id=quiz_id
    )

    db.session.add(new_question)
    db.session.commit()

    return redirect(url_for('view_questions', quiz_id=quiz_id))

@app.route('/update_question/<int:question_id>', methods=['POST'])
@login_required
def update_question(question_id):
    """ Update an existing question """
    question = Questions.query.get_or_404(question_id)
    new_text = request.form.get('question_statement')  # Change 'text' to 'question_statement'
    new_option_a = request.form.get("option_a")
    new_option_b = request.form.get("option_b")
    new_option_c = request.form.get("option_c")
    new_option_d = request.form.get("option_d")
    new_correct_option = request.form.get("correct_option")

    if new_text:
        question.question_statement = new_text  # Use correct column name
    if new_option_a:
        question.option1 = new_option_a
    if new_option_b:
        question.option2 = new_option_b
    if new_option_c:
        question.option3 = new_option_c
    if new_option_d:
        question.option4 = new_option_d
    if new_correct_option:
        question.correct_option = new_correct_option    

    db.session.commit()
    return redirect(url_for('view_questions', quiz_id=question.quiz_id))


@app.route('/delete_question/<int:question_id>', methods=['POST'])
@login_required
def delete_question(question_id):
    """ Delete a question """
    question = Questions.query.get_or_404(question_id)
    quiz_id = question.quiz_id
    db.session.delete(question)
    db.session.commit()
    
    return redirect(url_for('view_questions', quiz_id=quiz_id))



#__________TAKE QUIZ____________#
@app.route('/quiz/<int:quiz_id>', methods=['GET', 'POST'])
@login_required
def take_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = Questions.query.filter_by(quiz_id=quiz_id).all()
    
    if request.method == 'POST':
        total_score = 0
        option_map = {'1': 'A', '2': 'B', '3': 'C', '4': 'D'}
        for question in questions:
            selected_option = request.form.get(f'question_{question.id}')
            mapped_option = option_map.get(selected_option, "Invalid")
            
           
            if mapped_option == question.correct_option:  
                total_score+=1
          
            
       
        score_entry = Scores(
            quiz_id=quiz.id,
            user_id=current_user.id,
            time_stamp_of_attempt=datetime.now(), 
            total_scored=total_score
        )
        db.session.add(score_entry)
        db.session.commit()
        
        print("Score saved successfully!")  
        print(Scores.query.all())
        return redirect(url_for('scores'))  

    return render_template('take_quiz.html', quiz=quiz, questions=questions)

#____________--Display_of_Scores______________#
@app.route('/scores', methods=['GET'])
@login_required  
def scores():
    search_query = request.args.get('search', '').strip()  # Get search input
    user_scores = Scores.query.filter_by(user_id=current_user.id)  # Base Query
    search_error = None  # Placeholder for error message

    if search_query:
        if search_query.isdigit():  
            # Search by Quiz ID or Score if input is a number
            user_scores = user_scores.filter(
                (Scores.total_scored == int(search_query)))
            
        else:
            try:
                # Try parsing search query as a date (YYYY-MM-DD)
                search_date = datetime.strptime(search_query, '%Y-%m-%d').date()
                user_scores = user_scores.filter(
                    func.date(Scores.time_stamp_of_attempt) == search_date
                )
            except ValueError:
                # Search by quiz name (join Scores with Quiz)
                user_scores = user_scores.join(Quiz).filter(
                    Quiz.name.ilike(f"%{search_query}%")  # Case-insensitive search
                )

    user_scores = user_scores.all()  # Execute query

    return render_template(
        'scores.html', 
        scores=user_scores, 
        search_query=search_query, 
        search_error=search_error  
    )

#_________ADMIN SERACH___________#

@app.route('/search_subjects', methods=['POST'])
@login_required
def search_subjects():
    search_query = request.form.get('search_query', '').strip()
    subjects = Subject.query.filter(Subject.name.ilike(f"%{search_query}%")).all()
    
    return render_template('admin_dash.html', subjects=subjects, search_query=search_query)



@app.route('/search_chapters/<int:subject_id>', methods=['POST'])
@login_required
def search_chapters(subject_id):
    search_query = request.form.get('search_query', '').strip()
    subject = Subject.query.get_or_404(subject_id)
    
    chapters = Chapter.query.filter(
        Chapter.subject_id == subject_id,
        Chapter.name.ilike(f"%{search_query}%")
    ).all()
    
    return render_template('chapters.html', subject=subject, chapters=chapters, search_query=search_query)


@app.route('/search_quizzes/<int:chapter_id>', methods=['POST'])
@login_required
def search_quizzes(chapter_id):
    search_query = request.form.get('search_query', '').strip()
   
    chapter = Chapter.query.get_or_404(chapter_id)
    
    quizzes = Quiz.query.filter(
        Quiz.chapter_id == chapter_id,
        Quiz.name.ilike(f"%{search_query}%")
    ).all()

    
    return render_template('quizzes.html', chapter=chapter, quizzes=quizzes, search_query=search_query)


#_______________ADMIN_STATS__________________#
@app.route('/admin_stats')
def admin_stats():
    student = Student.query.all()
    subjects = Subject.query.all()
    chapters = Chapter.query.all()
    quiz = Quiz.query.all()


    num_subjects = len(subjects)
    num_chapters = len(chapters)
    num_quiz = len(quiz)
    all_students = len(student)

    active_quiz = sum(quiz_is_active(q.start_date, q.end_date) for q in quiz)
    inactive_quizzes = num_quiz - active_quiz

    plt.figure(figsize=(6, 4))
    plt.clf()
    categories = ['Subjects', 'Chapters', 'Quizzes','Students']
    counts = [num_subjects, num_chapters, num_quiz, all_students]
    plt.bar(categories, counts, color=['blue', 'green', 'orange', 'red'])
    plt.xlabel('Categories')
    plt.ylabel('Count')
    plt.title('Number of Subjects, Chapters, Quizzes, Students')
    ax = plt.gca()
    ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
    plt.xticks(ticks=range(len(categories)), labels=categories)
    plt.savefig('static/admin_stats.png')







    plt.figure(figsize=(6, 4))
    plt.clf()
    labels = ['Active Quizzes', 'Inactive Quizzes']
    sizes = [active_quiz, inactive_quizzes]
    colors = ['green', 'red']
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', colors=colors, startangle=90)
    plt.title('Active vs Inactive Quizzes')
    plt.savefig('static/quiz_status.png')

    return render_template("admin_stats.html")



#___________________USER _ STATS_______________#

from datetime import datetime

@app.route('/user_stats/<int:user_id>')
@login_required
def user_stats(user_id):
    student = Student.query.filter_by(student_id=user_id).first()
    if not student:
        return "User not found", 404

    quizzes = Quiz.query.all()  # Fetch all quizzes
    current_time = datetime.now()  # Get the current date & time

    # ✅ Detect Attempted Quizzes
    attempted_quizzes = [q for q in quizzes if Scores.query.filter_by(quiz_id=q.id, user_id=user_id).first()]

    # ✅ Detect Missed Quizzes (ended before current date & not attempted)
    missed_quizzes = [
        q for q in quizzes 
        if q.end_date < current_time.date() and q.id not in [aq.id for aq in attempted_quizzes]
    ]  

    # ✅ Count Attempted & Missed Quizzes
    attempted_count = len(attempted_quizzes)
    missed_count = len(missed_quizzes)

    print(f"Attempted Quizzes: {len(attempted_quizzes)}")
    print(f"Missed Quizzes: {len(missed_quizzes)}")
    
    # 📊 **Bar Chart: User Stats (Same Style as admin_stats)**
    plt.figure(figsize=(6, 4))
    plt.clf()
    categories = ['Attempted Quizzes', 'Missed Quizzes']
    counts = [attempted_count, missed_count]
    
    plt.bar(categories, counts, color=['green', 'red'])
    plt.xlabel('Quiz Status')
    plt.ylabel('Count')
    plt.title('User Quiz Participation')
    ax = plt.gca()
    ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
    plt.xticks(ticks=range(len(categories)), labels=categories)
    plt.savefig('static/bar_chart_path.png')  # ✅ Save Image in Static Folder
    

    return render_template(
        'user_stats.html')
        
    

    
