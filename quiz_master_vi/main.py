from flask import Flask, render_template
from flask import jsonify
from quiz_master_vi.controllers.database import db
from datetime import date, datetime  # Import datetime directly
from quiz_master_vi.controllers.config import config
from quiz_master_vi.sqlalchemy.sql import text
from quiz_master_vi.controllers.models import User, Admin
from quiz_master_vi.controllers.models import Subjects, Chapters, Questions, Options, QuizDetails, QuizResponse, Scores
from flask import request, redirect, url_for, session, flash
from flask import render_template
import os
import pandas as pd
from docx import Document
import PyPDF2
import re
import json

app = Flask(__name__, template_folder='templates',
            static_folder='static')  #provide the path of the templates folder

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
#app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False    # silence the deprecation warning
app.config.from_object(config)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create upload directory if it doesn't exist
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

db.init_app(app)
# The db object is an instance of the SQLAlchemy class. This object will be our entry point to the database.
with app.app_context():

    #db.drop_all()
    db.create_all()

    admin_user = Admin.query.filter_by(username='admin@gmail.com').first()
    if not admin_user:
        admin_user = Admin(username='admin@gmail.com', password='admin')
        db.session.add(admin_user)
        db.session.commit()


@app.route('/')
def hello_world():
    return render_template('index.html')


#render_template("registration.html")


@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'GET':
        return render_template('admin_login.html')

    if request.method == 'POST':
        # Get the username and password from the form
        username = request.form['username']
        password = request.form['password']

        # Check if both fields are filled
        if not username or not password:

            flash('Username and password are required', 'error')
            return redirect(url_for('admin_login'))

        # Check if the username is valid
        if '@' not in username:
            flash('Invalid username', 'error')
            return redirect(url_for('admin_login'))

        # Fetch admin user from the database
        admin_user = Admin.query.filter_by(username=username).first()

        # Validate credentials
        if admin_user and admin_user.password == password:
            session['admin'] = True  # Set admin session
            return redirect(
                url_for('adminhome'))  # Redirect to admin dashboard
        else:
            flash('Invalid credentials', 'error')
            return redirect(url_for('hello_world'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            session['user'] = True
            session['username'] = username
            return redirect(url_for('userdashboard'))
        else:
            flash('Invalid credentials', 'error')
            return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def user_register():
    if request.method == 'GET':
        return render_template('registeration.html')
    if request.method == 'POST':
        username = request.form['username']
        fullname = request.form['fullname']
        dob = request.form['dob']
        qualification = request.form.get('qualification')
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user:
            flash('User already exists', 'error')
            return redirect(url_for('user_register'))
        user = User(username=username,
                    fullname=fullname,
                    dob=dob,
                    qualification=qualification,
                    password=password)
        db.session.add(user)
        db.session.commit()
        flash('User registered successfully', 'success')
        return redirect(url_for('login'))


@app.route('/logout')
def logout():
    session.pop('admin', None)
    session.pop('user', None)  #clear the session
    flash('you have been logged out', 'info')
    return redirect(url_for('hello_world'))  # Redirect to admin login page


#don't use render template try to use redirect or url_for for homepage
@app.route('/adminhome')
def adminhome():
    subjects = Subjects.query.all()
    chapters = Chapters.query.all()
    return render_template('adminhome.html',
                           subjects=subjects,
                           chapters=chapters)


@app.route('/userhome')
def userhome():
    return render_template('userhome.html')


@app.route('/add_subject', methods=['GET', 'POST'])
def add_subject():
    if request.method == 'GET':
        return render_template('add_subject.html')
    if request.method == 'POST':
        subname = request.form['subject_name']
        desc = request.form['description']
        name = Subjects.query.filter_by(subject_name=subname).first()
        if name:
            flash('subject already exists')
            return render_template('add_subject.html')
        else:
            subject = Subjects(subject_name=subname, description=desc)
            db.session.add(subject)
            db.session.commit()
            flash("subject registered succesfully")
            return redirect(url_for('adminhome'))


@app.route('/add_chapter', methods=['GET', 'POST'])
def add_chapter():
    if request.method == 'GET':
        subjects = Subjects.query.all()
        return render_template('add_chapter.html', subjects=subjects)
    if request.method == 'POST':
        name = request.form.get('chapter_name')
        des = request.form.get('description')
        subject_name = request.form.get('Select_subject')
        #print(f"submitted subject is :{subject_name}")
        subject = Subjects.query.filter_by(subject_id=subject_name).first()
        if not subject:
            return "Error: Subject not found", 400

        subject_id = subject.subject_id  # Extract subject_id from database

        if not subject:
            return "Error: Subject not found", 400

        # Save chapter to database
        new_chapter = Chapters(chapter_name=name,
                               description=des,
                               subject_id=subject_id)
        db.session.add(new_chapter)
        db.session.commit()
    return redirect(url_for('adminhome'))


@app.route('/quiz')
def quiz():
    # Fetch chapters that have associated quizzes
    chapters_with_quizzes = Chapters.query.join(
        QuizDetails, Chapters.chaoter_id == QuizDetails.chapter_id).all()

    # Fetch all quizzes
    quizzes = QuizDetails.query.all()

    return render_template('quiz.html',
                           chapters=chapters_with_quizzes,
                           quizzes=quizzes)


@app.route('/add_quiz', methods=['GET', 'POST'])
def add_quiz():
    if request.method == 'GET':
        chap = Chapters.query.all()
        print(chap)
        return render_template('add_quiz.html', Chapters=chap)
    if request.method == 'POST':
        name = request.form['select_chapter']
        date = request.form['quiz_date']
        duration = request.form['duration']
        #chapter_id=Chapters.query.filter_by(choter_id=name).first()
        #if not chapter_id:
        #   return'chapter not found ',400
        new_quiz = QuizDetails(chapter_id=name,
                               quiz_date=date,
                               duration=duration)
        db.session.add(new_quiz)
        db.session.commit()
        return redirect(url_for('quiz'))


'''@app.route("/addquestion", methods=["GET", "POST"])
def addquestion():
    # Fetch all chapters to display in the form
    result = db.session.execute(text("SELECT * FROM chapters"))
    column_names = result.keys()
    chapters = [dict(zip(column_names, row)) for row in result.fetchall()]
    return render_template("addquestion.html", chapters=chapters, option4="Add", enumerate=enumerate, option5="add")'''


@app.route("/add_question", methods=["GET", "POST"])
def addcompletequestion():
    # Get form data
    if request.method == "GET":
        # Fetch all chapters to display in the form
        chapters = Chapters.query.all()
        return render_template("add_question.html", chapters=chapters)
    question_text = request.form.get("question_text")
    chapter_id = request.form.get("chapter_id")
    options = [
        request.form.get("option1"),
        request.form.get("option2"),
        request.form.get("option3"),
        request.form.get("option4"),
    ]
    correct_option = request.form.get("correct_option")

    # Validate inputs
    if not question_text or not chapter_id or not all(
            options) or not correct_option:
        return render_template(
            "addquestion.html",
            chapters=db.session.execute(
                text("SELECT * FROM chapters")).fetchall(),
            warningg="All fields are required.",
        )

    if not chapter_id.isdigit() or int(correct_option) not in range(1, 5):
        return render_template(
            "addquestion.html",
            chapters=db.session.execute(
                text("SELECT * FROM chapters")).fetchall(),
            warningg="Invalid chapter ID or correct option.",
        )

    try:
        # Create new question
        new_question = Questions(
            chapter_id=int(chapter_id),
            question=question_text,
        )
        db.session.add(new_question)
        db.session.commit()

        # Get the auto-generated question ID
        question_id = new_question.qid

        # Add all options for this question
        for option in options:
            new_option = Options(
                question_id=question_id,
                option=option,
            )
            db.session.add(new_option)
        db.session.commit()

        # Set the correct answer
        corr = options[int(correct_option) - 1]
        result2 = db.session.execute(
            text(
                "select option_id from options where option=:option and question_id= :question_id"
            ), {
                "option": corr,
                "question_id": question_id
            })
        opt_id = result2.scalar()

        db.session.execute(
            text(
                "UPDATE questions SET answer = :opt_id WHERE qid = :question_id"
            ), {
                "opt_id": opt_id,
                "question_id": question_id
            })
        db.session.commit()

        return redirect("/questions")
    except Exception as e:
        db.session.rollback()
        return f"Error: {e}"


# Utility functions (add near the top with other imports)
def get_user_id(username):
    """Get user ID from username"""
    result = db.session.execute(
        text("SELECT uid FROM user WHERE username = :username"),
        {"username": username})
    return result.scalar()  # Returns None if user doesn't exist


def get_attempted_quizzes(user_id):
    """Get set of attempted quiz IDs"""
    result = db.session.execute(
        text("SELECT DISTINCT quizid FROM quizresponse WHERE uid = :uid"),
        {"uid": user_id})
    return {row[0] for row in result}  # Return as set


def row_to_dict(row):
    """Convert a SQLAlchemy Row object to a dictionary."""
    return dict(row._mapping) if row else None


def rows_to_dicts(rows):
    """Convert a list of SQLAlchemy Row objects to a list of dictionaries."""
    return [dict(row._mapping) for row in rows]


def allowed_file(filename):
    """Check if file extension is allowed"""
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx', 'csv', 'json'}
    return '.' in filename and filename.rsplit(
        '.', 1)[1].lower() in ALLOWED_EXTENSIONS


def extract_text_from_pdf(file_path):
    """Extract text from PDF file"""
    text = ""
    with open(file_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text


def extract_text_from_docx(file_path):
    """Extract text from DOCX file"""
    doc = Document(file_path)
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text


def parse_questions_from_text(text):
    """Parse questions from text using simple patterns"""
    questions = []

    # Pattern for questions with options (Q: question? A) option1 B) option2 C) option3 D) option4 Answer: A)
    pattern = r'Q[:\.]?\s*(.+?)\s*[Aa]\)\s*(.+?)\s*[Bb]\)\s*(.+?)\s*[Cc]\)\s*(.+?)\s*[Dd]\)\s*(.+?)\s*Answer[:\s]*([A-Da-d])'

    matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)

    for match in matches:
        question_text = match[0].strip()
        options = [
            match[1].strip(), match[2].strip(), match[3].strip(),
            match[4].strip()
        ]
        correct_answer = match[5].upper()

        # Convert letter to number (A=1, B=2, C=3, D=4)
        correct_option = ord(correct_answer) - ord('A') + 1

        questions.append({
            'question': question_text,
            'options': options,
            'correct_option': correct_option
        })

    return questions


def parse_questions_from_csv(file_path):
    """Parse questions from CSV file"""
    questions = []
    try:
        df = pd.read_csv(file_path)

        # Expected columns: question, option1, option2, option3, option4, correct_option
        required_columns = [
            'question', 'option1', 'option2', 'option3', 'option4',
            'correct_option'
        ]

        if all(col in df.columns for col in required_columns):
            for _, row in df.iterrows():
                questions.append({
                    'question':
                    str(row['question']).strip(),
                    'options': [
                        str(row['option1']).strip(),
                        str(row['option2']).strip(),
                        str(row['option3']).strip(),
                        str(row['option4']).strip()
                    ],
                    'correct_option':
                    int(row['correct_option'])
                })
    except Exception as e:
        print(f"Error parsing CSV: {e}")

    return questions


def parse_questions_from_json(file_path):
    """Parse questions from JSON file"""
    questions = []
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)

        if isinstance(data, list):
            for item in data:
                if all(key in item
                       for key in ['question', 'options', 'correct_option']):
                    questions.append({
                        'question': item['question'],
                        'options': item['options'][:4],  # Take first 4 options
                        'correct_option': item['correct_option']
                    })
    except Exception as e:
        print(f"Error parsing JSON: {e}")

    return questions


@app.route('/upload_questions', methods=['GET', 'POST'])
def upload_questions():
    if request.method == 'GET':
        chapters = Chapters.query.all()
        return render_template('upload_questions.html', chapters=chapters)

    if request.method == 'POST':
        # Check if file was uploaded
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return redirect(request.url)

        file = request.files['file']
        chapter_id = request.form.get('chapter_id')

        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)

        if not chapter_id:
            flash('Please select a chapter', 'error')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = file.filename
            if not filename or not isinstance(filename, str):
                flash('Invalid file name. Please select a valid file.', 'error')
                return redirect(request.url)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            # Extract questions based on file type
            questions = []
            try:
                if filename.lower().endswith('.pdf'):
                    text_content = extract_text_from_pdf(file_path)
                    questions = parse_questions_from_text(text_content)
                elif filename.lower().endswith('.docx'):
                    text_content = extract_text_from_docx(file_path)
                    questions = parse_questions_from_text(text_content)
                elif filename.lower().endswith('.csv'):
                    questions = parse_questions_from_csv(file_path)
                elif filename.lower().endswith('.json'):
                    questions = parse_questions_from_json(file_path)
                elif filename.lower().endswith('.txt'):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        text_content = f.read()
                    questions = parse_questions_from_text(text_content)

                # Save questions to database
                added_count = 0
                for q_data in questions:
                    try:
                        if q_data['question'] and len(q_data['options']) == 4:
                            # Check if chapter exists
                            chapter = Chapters.query.filter_by(chaoter_id=int(chapter_id)).first()
                            if not chapter:
                                flash('Selected chapter does not exist.', 'error')
                                continue
                            # Create new question
                            new_question = Questions(chapter_id=int(chapter_id), question=q_data['question'])
                            db.session.add(new_question)
                            db.session.commit()

                            # Add options
                            for option_text in q_data['options']:
                                new_option = Options(question_id=new_question.qid, option=option_text)
                                db.session.add(new_option)
                            db.session.commit()

                            # Set correct answer
                            correct_option_text = q_data['options'][q_data['correct_option'] - 1]
                            result = db.session.execute(
                                text("SELECT option_id FROM options WHERE option = :option AND question_id = :question_id"),
                                {"option": correct_option_text, "question_id": new_question.qid}
                            )
                            opt_id = result.scalar()

                            if opt_id:
                                new_question.answer = opt_id
                                db.session.commit()
                                added_count += 1
                        else:
                            flash(f'Invalid question or options format: {q_data}', 'warning')
                    except Exception as e:
                        db.session.rollback()
                        flash(f'Error adding question: {q_data.get("question", "?")} - {str(e)}', 'danger')

                # Clean up uploaded file
                os.remove(file_path)

                if added_count > 0:
                    flash(f'Successfully added {added_count} questions from the file!', 'success')
                else:
                    flash('No valid questions found in the file. Please check the format.', 'warning')

                return redirect(url_for('questions'))
            except Exception as e:
                flash(f'Error processing file: {str(e)}', 'error')
                # Clean up file on error
                if os.path.exists(file_path):
                    os.remove(file_path)
                return redirect(request.url)
        else:
            flash(
                'Invalid file type. Please upload PDF, DOCX, CSV, JSON, or TXT files only.',
                'error')
            return redirect(request.url)


@app.route('/questions', methods=['GET', 'POST'])
def questions():
    if request.method == 'GET':
        chapters = Chapters.query.all()
    quizzes = QuizDetails.query.all()
    questions = Questions.query.all()
    return render_template('question.html',
                           chapters=chapters,
                           quizzes=quizzes,
                           questions=questions)


@app.route('/chapters', methods=['GET', 'POST'])
def chapters():
    if request.method == 'GET':
        chapter = Chapters.query.all()
        subject = Subjects.query.all()
        return render_template('chapters.html',
                               chapters=chapter,
                               subjects=subject)


@app.route('/student_personal_details.html', methods=['GET', 'POST'])
def student_personal_details():
    users = User.query.all()
    return render_template('student_personal_details.html', users=users)


@app.route('/edit_chapter/<int:chapter_id>', methods=['GET', 'POST'])
def edit_chapter(chapter_id):
    chapter = Chapters.query.get_or_404(
        chapter_id)  #get the chapter, or return 404 if not found

    if request.method == 'POST':
        chapter.chapter_name = request.form['chapter_name']
        db.session.commit()
        return redirect(url_for('adminhome'))  #redirect to home page

    return render_template('editchapters.html',
                           chapter=chapter,
                           chapter_id=chapter_id)


@app.route('/edit_quiz/<int:quizid>', methods=['GET', 'POST'])
def edit_quiz(quizid):
    quiz = QuizDetails.query.get_or_404(quizid)

    if request.method == 'POST':
        quiz.quiz_date = request.form['quiz_date']
        quiz.duration = request.form['duration']
        db.session.commit()
        return redirect(url_for('quiz'))  # Redirect to appropriate page

    return render_template('edit_quiz.html', quiz=quiz)


@app.route('/edit_question/<int:question_id>', methods=['GET', 'POST'])
def edit_question(question_id):
    question = Questions.query.get_or_404(question_id)

    if request.method == 'POST':
        question.question = request.form['question']
        question.answer = request.form['answer']

        # Update options
        for option_id, option_text in request.form.items():
            if option_id.startswith('options['):
                option_id = int(option_id[8:-1])
                option = Options.query.get(option_id)
                if option:
                    option.option = option_text
        db.session.commit()
        return redirect(url_for('questions'))

    return render_template('edit_question.html', question=question)


@app.route('/delete_option/<int:option_id>')
def delete_option(option_id):
    option = Options.query.get_or_404(option_id)
    db.session.delete(option)
    db.session.commit()
    return redirect(url_for('edit_question', question_id=option.question_id))


@app.route('/delete_chapter/<int:chapter_id>', methods=['GET', 'POST'])
def delete_chapter(chapter_id):
    chapter = Chapters.query.get_or_404(chapter_id)

    if request.method == 'POST':
        db.session.delete(chapter)
        db.session.commit()
        return redirect(url_for('adminhome'))

    return render_template('delete_chapter.html', chapter=chapter)


@app.route('/delete_question/<int:question_id>', methods=['GET', 'POST'])
def delete_question(question_id):
    question = Questions.query.get_or_404(question_id)

    if request.method == 'POST':
        db.session.delete(question)
        db.session.commit()
        return redirect(url_for('adminhome'))

    return render_template('delete_question.html', question=question)


@app.route('/delete_quiz/<int:quiz_id>', methods=['GET', 'POST'])
def delete_quiz(quiz_id):
    quiz = QuizDetails.query.get_or_404(quiz_id)

    if request.method == 'POST':
        db.session.delete(quiz)
        db.session.commit()
        return redirect(url_for('adminhome'))  # Redirect to appropriate page

    return render_template('delete_quiz.html', quiz=quiz)


#started the user_dashboard
@app.route('/user', methods=['GET', 'POST'])
def userdashboard():
    if request.method == 'GET':
        subject = Subjects.query.all()
        chapter = Chapters.query.all()
        return render_template('user.html', subjects=subject, chapters=chapter)


@app.route('/livequiz')
def livequiz():
    # Get current date and user ID
    current_date = date.today()

    user_id = get_user_id(session['username'])  # Your user lookup function

    # Fetch available quizzes
    quizzes = db.session.execute(
        text("""
        SELECT q.quizid, q.quiz_date, q.duration, 
               c.chapter_name, s.subject_name
        FROM quiz_details q
        JOIN chapters c ON q.chapter_id = c.chaoter_id
        JOIN subjects s ON c.subject_id = s.subject_id
        WHERE q.quiz_date >= :current_date
        ORDER BY q.quiz_date
    """), {
            "current_date": current_date
        }).fetchall()

    # Check attempted quizzes
    attempted = get_attempted_quizzes(
        user_id)  # Your function to fetch attempted quizzes

    return render_template(
        'livequiz.html',
        mode='list',  # Flag to show quiz list
        quizzes=quizzes,
        attempted=attempted)


@app.route('/start_quiz/<int:quiz_id>')
def start_quiz(quiz_id):
    # Verify quiz is available
    quiz = QuizDetails.query.filter(QuizDetails.quizid == quiz_id,
                                    QuizDetails.quiz_date
                                    >= date.today()).first_or_404()

    # Get questions and options
    questions = Questions.query.filter_by(chapter_id=quiz.chapter_id).all()
    questions_data = []
    for q in questions:
        options = Options.query.filter_by(question_id=q.qid).all()
        questions_data.append({
            "qid": q.qid,
            "question": q.question,
            "options": options  # Correct key name
        })

    return render_template(
        'livequiz.html',
        mode='quiz',  # Flag to show questions
        quiz=quiz,
        questions=questions_data,
        duration=quiz.duration,
    )


# ... (Flask app setup and other routes)


@app.route('/submit_quiz/<int:quiz_id>', methods=['POST'])
def submit_quiz(quiz_id):
    # 1. Verify user is logged in
    if 'username' not in session:
        return redirect(url_for('login'))

    # 2. Get user ID
    user_id = db.session.execute(
        text("SELECT uid FROM user WHERE username = :username"), {
            "username": session['username']
        }).scalar()

    if not user_id:
        flash("User not found", "error")
        return redirect(url_for('login'))

    # 3. Check if already attempted
    existing_attempt = db.session.execute(
        text(
            "SELECT 1 FROM quizresponse WHERE quizid = :quiz_id AND uid = :uid"
        ), {
            "quiz_id": quiz_id,
            "uid": user_id
        }).fetchone()

    if existing_attempt:
        flash("You've already taken this quiz", "warning")
        return redirect(
            url_for('quiz_results', quiz_id=quiz_id, user_id=user_id))

    # 4. Process answers
    score = 0
    questions = db.session.execute(
        text("SELECT qid, answer FROM questions WHERE chapter_id = "
             "(SELECT chapter_id FROM quiz_details WHERE quizid = :quiz_id)"),
        {
            "quiz_id": quiz_id
        }).fetchall()

    for question in questions:
        answer_key = f"answer_{question.qid}"
        user_answer = request.form.get(answer_key)

        if user_answer is not None and user_answer != '':
            if int(user_answer) == question.answer:
                score += 1
            # Save all responses (even incorrect, but only if answered)
            response = QuizResponse(quizid=quiz_id,
                                    uid=user_id,
                                    questionid=question.qid,
                                    optionid=int(user_answer))
            db.session.add(response)

    # 5. Save final score
    total_questions = len(questions)
    db.session.add(
        Scores(
            quiz_id=quiz_id,
            uid=user_id,
            score=score,
            total=total_questions,
            time_stamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ))
    db.session.commit()

    # 6. Redirect to results
    return redirect(url_for('quiz_results', quiz_id=quiz_id, user_id=user_id))


@app.route('/quiz_results/<int:quiz_id>/<int:user_id>', methods=['GET'])
def quiz_results(quiz_id, user_id):
    # Fetch necessary data for the template
    quiz_details = db.session.execute(
        text("""
            SELECT q.quizid, q.quiz_date, c.chapter_name, s.subject_name
            FROM quiz_details q
            JOIN chapters c ON q.chapter_id = c.chaoter_id
            JOIN subjects s ON c.subject_id = s.subject_id
            WHERE q.quizid = :quiz_id
        """), {
            "quiz_id": quiz_id
        }).fetchone()
    quiz_details = row_to_dict(quiz_details)

    user_details = db.session.execute(
        text("SELECT * FROM user WHERE uid = :uid"), {
            "uid": user_id
        }).fetchone()
    user_details = row_to_dict(user_details)

    responses = db.session.execute(
        text("""
            SELECT q.question, r.optionid AS user_answer, q.answer AS correct_answer
            FROM quizresponse r
            JOIN questions q ON r.questionid = q.qid
            WHERE r.quizid = :quiz_id AND r.uid = :uid
        """), {
            "quiz_id": quiz_id,
            "uid": user_id
        }).fetchall()
    responses = rows_to_dicts(responses)

    # Calculate total questions and score
    total = len(responses)  # Total number of questions
    score = sum(1 for response in responses if response['user_answer'] ==
                response['correct_answer'])  # Correct answers

    # Define dynamic variables
    dynamic_name2 = 'user_register'  # Replace with the actual route name
    dynamic_name3 = 'Register New User'  # Replace with the actual button text

    return render_template(
        'quiz_results.html',
        quiz_details=quiz_details,
        user_details=user_details,
        responses=responses,
        total=total,  # Pass total to the template
        score=score,  # Pass score to the template
        dynamic_name2=dynamic_name2,
        dynamic_name3=dynamic_name3)


@app.route('/edit_subject/<int:subject_id>', methods=['GET', 'POST'])
def edit_subject(subject_id):
    subject = Subjects.query.get_or_404(subject_id)

    if request.method == 'POST':
        subject.subject_name = request.form['subject_name']
        subject.description = request.form['description']
        db.session.commit()
        return redirect(url_for('adminhome'))

    return render_template('edit_subject.html', subject=subject)


@app.route('/delete_subject/<int:subject_id>', methods=['GET', 'POST'])
def delete_subject(subject_id):
    subject = Subjects.query.get_or_404(subject_id)
    if request.method == 'GET':
        return render_template('delete_subject.html', subject=subject)
    if request.method == 'POST':
        db.session.delete(subject)
        db.session.commit()
        return redirect(url_for('adminhome'))


@app.route("/student_academic_details", methods=["GET"])
def student_academic_details():
    username = session.get('username')
    if not username:
        pythonflash("Please log in", "error")
        return redirect(url_for('login'))

    # Get user ID
    user_id = db.session.execute(
        text("SELECT uid FROM user WHERE username = :username"), {
            "username": username
        }).scalar()

    if not user_id:
        flash("User not found", "error")
        return redirect(url_for('login'))

    # Convert all results to serializable dictionaries
    def row_to_dict(row):
        return {key: getattr(row, key) for key in row._fields}

    # Quiz details
    quizdetails = [
        row_to_dict(row) for row in db.session.execute(
            text("""
        SELECT s.quiz_id as quizid, c.chapter_name, q.quiz_date, 
               q.duration, s.score, s.total
        FROM scores s
        JOIN quiz_details q ON s.quiz_id = q.quizid
        JOIN chapters c ON q.chapter_id = c.chaoter_id
        WHERE s.uid = :uid
    """), {"uid": user_id})
    ]

    # Subject counts
    subjectcount = [
        row_to_dict(row) for row in db.session.execute(
            text("""
        SELECT s.subject_name, COUNT(*) as count
        FROM subjects s
        JOIN chapters c ON s.subject_id = c.subject_id
        JOIN quiz_details q ON c.chaoter_id = q.chapter_id
        JOIN scores sc ON q.quizid = sc.quiz_id
        WHERE sc.uid = :uid
        GROUP BY s.subject_name
    """), {"uid": user_id})
    ]

    # Subject averages
    subjectmarks = [
        row_to_dict(row) for row in db.session.execute(
            text("""
        SELECT s.subject_name, AVG(sc.score) as avg
        FROM scores sc
        JOIN quiz_details q ON sc.quiz_id = q.quizid
        JOIN chapters c ON q.chapter_id = c.chaoter_id
        JOIN subjects s ON c.subject_id = s.subject_id
        WHERE sc.uid = :uid
        GROUP BY s.subject_name
    """), {"uid": user_id})
    ]

    return render_template("student_academic_details.html",
                           quizdetails=quizdetails,
                           subjectcount=subjectcount,
                           subjectmarks=subjectmarks,
                           uid=user_id,
                           message="Your Academic Performance")


@app.route('/transcript/<int:quiz_id>/<int:uid>', methods=['GET'])
def transcript(quiz_id, uid):
    # Fetch quiz and user details
    quiz_details = db.session.execute(
        text("""
            SELECT q.quizid, q.quiz_date, c.chapter_name, s.subject_name
            FROM quiz_details q
            JOIN chapters c ON q.chapter_id = c.chaoter_id
            JOIN subjects s ON c.subject_id = s.subject_id
            WHERE q.quizid = :quiz_id
        """), {
            "quiz_id": quiz_id
        }).fetchone()
    quiz_details = row_to_dict(quiz_details)

    user_details = db.session.execute(
        text("SELECT * FROM user WHERE uid = :uid"), {
            "uid": uid
        }).fetchone()
    user_details = row_to_dict(user_details)

    # Fetch user's responses
    responses = db.session.execute(
        text("""
            SELECT q.question, r.optionid AS user_answer, q.answer AS correct_answer
            FROM quizresponse r
            JOIN questions q ON r.questionid = q.qid
            WHERE r.quizid = :quiz_id AND r.uid = :uid
        """), {
            "quiz_id": quiz_id,
            "uid": uid
        }).fetchall()
    responses = rows_to_dicts(responses)

    return render_template('transcript.html',
                           quiz_details=quiz_details,
                           user_details=user_details,
                           responses=responses)


@app.route('/admin/search', methods=['GET'])
def admin_search():
    # Get the search query and type from the request
    search_query = request.args.get('query', '').strip()
    search_type = request.args.get('type', '').strip()

    # Initialize results
    results = []

    # Handle different search types
    if search_type == 'users':
        # Search for users by username or fullname
        results = User.query.filter(
            (User.username.ilike(f'%{search_query}%'))
            | (User.fullname.ilike(f'%{search_query}%'))).all()

    elif search_type == 'subjects':
        # Search for subjects by subject_name
        results = Subjects.query.filter(
            Subjects.subject_name.ilike(f'%{search_query}%')).all()

    elif search_type == 'quizzes':
        # Search for quizzes by quiz ID or related subject name
        results = QuizDetails.query.join(Chapters, QuizDetails.chapter_id == Chapters.chaoter_id) \
            .join(Subjects, Chapters.subject_id == Subjects.subject_id) \
            .filter(
                (QuizDetails.quizid.ilike(f'%{search_query}%')) |
                (Subjects.subject_name.ilike(f'%{search_query}%'))
            ).all()

    elif search_type == 'questions':
        # Search for questions by question text
        results = Questions.query.filter(
            Questions.question.ilike(f'%{search_query}%')).all()

    else:
        # Invalid search type
        flash('Invalid search type provided.', 'danger')
        return redirect(url_for('admin_dashboard'))

    # Render the search results page
    return render_template('admin_search_results.html',
                           results=results,
                           search_type=search_type)


@app.route('/user/search', methods=['GET'])
def user_search():
    # Get the search query and type from the request
    search_query = request.args.get('query', '').strip()
    search_type = request.args.get('type', '').strip()

    # Initialize results
    results = []

    # Handle different search types
    if search_type == 'subjects':
        # Search for subjects by subject_name
        results = Subjects.query.filter(
            Subjects.subject_name.ilike(f'%{search_query}%')).all()

    elif search_type == 'quizzes':
        # Search for quizzes by quiz ID or related subject name
        results = QuizDetails.query.join(Chapters, QuizDetails.chapter_id == Chapters.chaoter_id) \
            .join(Subjects, Chapters.subject_id == Subjects.subject_id) \
            .filter(
                (QuizDetails.quizid.ilike(f'%{search_query}%')) |
                (Subjects.subject_name.ilike(f'%{search_query}%'))
            ).all()

    elif search_type == 'questions':
        # Search for questions by question text
        results = Questions.query.filter(
            Questions.question.ilike(f'%{search_query}%')).all()

    else:
        # Invalid search type
        flash('Invalid search type provided.', 'danger')
        return redirect(url_for('userhome'))

    # Render the search results page
    return render_template('user_search_results.html',
                           results=results,
                           search_type=search_type)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5005, debug=True)
