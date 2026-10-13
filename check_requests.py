from app import app
from extensions import db
from models import FoodRequest

with app.app_context():
    requests = FoodRequest.query.all()
    for r in requests:
        print(r.id, r.student_id, r.food_category, r.quantity_needed, r.urgency, r.status)