from app import app
from extensions import db
from models import FoodResource

with app.app_context():
    resources = FoodResource.query.all()
    for r in resources:
        print(r.id, r.donor_id, r.food_category, r.quantity_available, r.expiry_date, r.status)