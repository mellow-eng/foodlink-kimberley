from app import app
from extensions import db
from models import Student

with app.app_context():
    students = Student.query.all()
    for s in students:
        print(s.id, s.full_name, s.email, s.location)