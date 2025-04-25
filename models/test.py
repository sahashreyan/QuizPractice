from datetime import datetime
from . import db

class Test(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    duration_minutes = db.Column(db.Integer, nullable=False)
    has_negative_marking = db.Column(db.Boolean, default=False)
    negative_marks = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))

    # Relationships
    questions = db.relationship('Question', backref='test', lazy='dynamic', cascade='all, delete-orphan')
    results = db.relationship('Result', backref='test', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Test {self.title}>'

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    test_id = db.Column(db.Integer, db.ForeignKey('test.id'), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.Text, nullable=False)
    option_b = db.Column(db.Text, nullable=False)
    option_c = db.Column(db.Text, nullable=False)
    option_d = db.Column(db.Text, nullable=False)
    correct_option = db.Column(db.String(1), nullable=False)  # 'A', 'B', 'C', or 'D'
    marks = db.Column(db.Float, default=1.0)

    # Relationship with answers
    answers = db.relationship('Answer', backref='question', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Question {self.id} for Test {self.test_id}>'