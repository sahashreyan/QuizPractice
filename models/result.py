from datetime import datetime
from . import db

class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    test_id = db.Column(db.Integer, db.ForeignKey('test.id'), nullable=False)
    score = db.Column(db.Float, default=0)
    total_possible = db.Column(db.Float)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    completed = db.Column(db.Boolean, default=False)

    # Relationship with answers
    answers = db.relationship('Answer', backref='result', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Result {self.id} User {self.user_id} Test {self.test_id}>'

class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    result_id = db.Column(db.Integer, db.ForeignKey('result.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    selected_option = db.Column(db.String(1))  # 'A', 'B', 'C', 'D', or None if unanswered
    is_correct = db.Column(db.Boolean)
    marks_obtained = db.Column(db.Float)

    def __repr__(self):
        return f'<Answer {self.id} for Question {self.question_id}>'