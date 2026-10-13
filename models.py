from extensions import db
from flask_login import UserMixin
from datetime import datetime

class Student(UserMixin, db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    location = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    requests = db.relationship('FoodRequest', backref='student', lazy=True)
    role = 'student'

    def get_id(self):
        return f"student-{self.id}"


class Donor(UserMixin, db.Model):
    __tablename__ = 'donors'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    location = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    resources = db.relationship('FoodResource', backref='donor', lazy=True)
    role = 'donor'

    def get_id(self):
        return f"donor-{self.id}"


class FoodRequest(db.Model):
    __tablename__ = 'food_requests'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    food_category = db.Column(db.String(80), nullable=False)
    quantity_needed = db.Column(db.Integer, nullable=False)
    urgency = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class FoodResource(db.Model):
    __tablename__ = 'food_resources'
    id = db.Column(db.Integer, primary_key=True)
    donor_id = db.Column(db.Integer, db.ForeignKey('donors.id'), nullable=False)
    food_category = db.Column(db.String(80), nullable=False)
    quantity_available = db.Column(db.Integer, nullable=False)
    expiry_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), default='available')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)