from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.urls import url_parse 

import os
from datetime import datetime

from config import Config
from models import db
from models.user import User
from models.test import Test, Question
from models.result import Result, Answer

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize database
db.init_app(app)

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create database tables
@app.before_first_request
def create_tables():
    db.create_all()
    # Create admin user if none exists
    if not User.query.filter_by(is_admin=True).first():
        admin = User(username='admin', email='admin@example.com', is_admin=True)
        admin.set_password('admin123')  # Change this in production!
        db.session.add(admin)
        db.session.commit()

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user is None or not user.check_password(password):
            flash('Invalid username or password')
            return redirect(url_for('login'))

        login_user(user, remember=True)
        next_page = request.args.get('next')

        if not next_page or url_parse(next_page).netloc != '':
            if user.is_admin:
                next_page = url_for('admin_dashboard')
            else:
                next_page = url_for('student_dashboard')

        return redirect(next_page)

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# Admin routes
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        abort(403)
    tests = Test.query.all()
    return render_template('admin/dashboard.html', tests=tests)

@app.route('/admin/users')
@login_required
def manage_users():
    if not current_user.is_admin:
        abort(403)
    users = User.query.all()
    return render_template('admin/manage_users.html', users=users)

@app.route('/admin/create_user', methods=['GET', 'POST'])
@login_required
def create_user():
    if not current_user.is_admin:
        abort(403)

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        is_admin = 'is_admin' in request.form

        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('create_user'))

        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return redirect(url_for('create_user'))

        user = User(username=username, email=email, is_admin=is_admin)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash('User created successfully')
        return redirect(url_for('manage_users'))

    return render_template('admin/create_user.html')

@app.route('/admin/create_test', methods=['GET', 'POST'])
@login_required
def create_test():
    if not current_user.is_admin:
        abort(403)

    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        duration = int(request.form.get('duration'))
        has_negative_marking = 'negative_marking' in request.form
        negative_marks = float(request.form.get('negative_marks', 0))

        # Create test
        test = Test(
            title=title,
            description=description,
            duration_minutes=duration,
            has_negative_marking=has_negative_marking,
            negative_marks=negative_marks if has_negative_marking else 0,
            created_by=current_user.id
        )
        db.session.add(test)
        db.session.flush()  # Get the test ID without committing yet

        # Process questions
        questions_data = {}
        for key, value in request.form.items():
            if key.startswith('questions['):
                # Parse the key format: questions[1][text], questions[1][option_a], etc.
                parts = key.rstrip(']').split('[')
                if len(parts) == 3:
                    q_index = parts[1]
                    q_field = parts[2]

                    if q_index not in questions_data:
                        questions_data[q_index] = {}

                    questions_data[q_index][q_field] = value

        # Create questions
        for _, q_data in questions_data.items():
            if 'text' in q_data:  # Ensure it's a complete question
                question = Question(
                    test_id=test.id,
                    question_text=q_data.get('text', ''),
                    option_a=q_data.get('option_a', ''),
                    option_b=q_data.get('option_b', ''),
                    option_c=q_data.get('option_c', ''),
                    option_d=q_data.get('option_d', ''),
                    correct_option=q_data.get('correct', 'A'),
                    marks=float(q_data.get('marks', 1))
                )
                db.session.add(question)

        db.session.commit()
        flash('Test created successfully')
        return redirect(url_for('admin_dashboard'))

    return render_template('admin/create_test.html')

@app.route('/admin/test/<int:test_id>/results')
@login_required
def admin_view_results(test_id):
    if not current_user.is_admin:
        abort(403)

    test = Test.query.get_or_404(test_id)
    results = Result.query.filter_by(test_id=test_id, completed=True).all()

    return render_template('admin/view_results.html', test=test, results=results)

@app.route('/admin/test/<int:test_id>/delete', methods=['POST'])
@login_required
def delete_test(test_id):
    if not current_user.is_admin:
        abort(403)

    test = Test.query.get_or_404(test_id)

    # Delete the test and all related questions, answers, and results
    db.session.delete(test)
    db.session.commit()

    flash('Test deleted successfully')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/user/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        abort(403)

    user = User.query.get_or_404(user_id)

    # Prevent deleting oneself
    if user.id == current_user.id:
        flash('You cannot delete your own account')
        return redirect(url_for('manage_users'))

    # Delete the user and all related results and answers
    db.session.delete(user)
    db.session.commit()

    flash('User deleted successfully')
    return redirect(url_for('manage_users'))

# Student routes
@app.route('/student/dashboard')
@login_required
def student_dashboard():
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))

    # Get all available tests
    available_tests = Test.query.all()

    # Get all completed tests for the current user
    completed_tests = Result.query.filter_by(
        user_id=current_user.id,
        completed=True
    ).all()

    return render_template('student/dashboard.html',
                          available_tests=available_tests,
                          completed_tests=completed_tests)


@app.route('/student/test/<int:test_id>', methods=['GET'])
@login_required
def take_test(test_id):
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))

    test = Test.query.get_or_404(test_id)

    # Check if user has already completed this test
    existing_result = Result.query.filter_by(
        user_id=current_user.id,
        test_id=test_id,
        completed=True
    ).first()

    if existing_result:
        flash('You have already completed this test')
        return redirect(url_for('view_test_result', result_id=existing_result.id))

    # Create or get an in-progress result
    result = Result.query.filter_by(
        user_id=current_user.id,
        test_id=test_id,
        completed=False
    ).first()

    if not result:
        # Create a new result record
        result = Result(
            user_id=current_user.id,
            test_id=test_id,
            start_time=datetime.utcnow(),
            total_possible=sum([q.marks for q in test.questions])
        )
        db.session.add(result)
        db.session.commit()

    questions = test.questions.all()

    return render_template('student/take_test.html',
                          test=test,
                          questions=questions,
                          result=result)

@app.route('/student/test/<int:test_id>/submit', methods=['POST'])
@login_required
def submit_test(test_id):
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))

    test = Test.query.get_or_404(test_id)
    result_id = request.form.get('result_id')
    result = Result.query.get_or_404(result_id)

    # Verify the result belongs to the current user
    if result.user_id != current_user.id:
        abort(403)

    # Process answers
    answers_data = {}
    for key, value in request.form.items():
        if key.startswith('answers['):
            # Parse question ID from answers[id]
            q_id = key.replace('answers[', '').replace(']', '')
            answers_data[q_id] = value

    # Calculate score
    total_score = 0
    questions = test.questions.all()

    for question in questions:
        q_id = str(question.id)
        selected_option = answers_data.get(q_id)
        is_correct = selected_option == question.correct_option

        # Calculate marks for this answer
        if selected_option:
            if is_correct:
                marks = question.marks
            else:
                marks = -test.negative_marks if test.has_negative_marking else 0
        else:
            marks = 0

        total_score += marks

        # Create or update answer record
        answer = Answer.query.filter_by(
            result_id=result.id,
            question_id=question.id
        ).first()

        if not answer:
            answer = Answer(
                result_id=result.id,
                question_id=question.id,
                selected_option=selected_option,
                is_correct=is_correct,
                marks_obtained=marks
            )
            db.session.add(answer)
        else:
            answer.selected_option = selected_option
            answer.is_correct = is_correct
            answer.marks_obtained = marks

    # Update result record
    result.score = max(0, total_score)  # Ensure score is not negative
    result.end_time = datetime.utcnow()
    result.completed = True

    db.session.commit()

    return redirect(url_for('view_test_result', result_id=result.id))

@app.route('/student/result/<int:result_id>')
@login_required
def view_test_result(result_id):
    result = Result.query.get_or_404(result_id)

    # Verify the result belongs to the current user
    if result.user_id != current_user.id and not current_user.is_admin:
        abort(403)

    test = Test.query.get(result.test_id)
    answers = Answer.query.filter_by(result_id=result.id).all()

    return render_template('student/test_results.html',
                          result=result,
                          test=test,
                          answers=answers)




# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(403)
def forbidden_error(error):
    return render_template('errors/403.html'), 403

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Create admin user if none exists
        if not User.query.filter_by(is_admin=True).first():
            admin = User(username='admin', email='admin@example.com', is_admin=True)
            admin.set_password('admin123')  # Change this in production!
            db.session.add(admin)
            db.session.commit()
            print('Admin user created with username: admin and password: admin123')
    app.run(debug=True)