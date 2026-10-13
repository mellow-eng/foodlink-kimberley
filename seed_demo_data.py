from app import app
from extensions import db
from models import FoodRequest
from datetime import datetime, timedelta

with app.app_context():
    base_date = datetime.utcnow() - timedelta(days=14)

    demo_requests = [
        FoodRequest(student_id=1, food_category="grains", quantity_needed=3, urgency="low", created_at=base_date),
        FoodRequest(student_id=1, food_category="grains", quantity_needed=5, urgency="medium", created_at=base_date + timedelta(days=4)),
        FoodRequest(student_id=1, food_category="grains", quantity_needed=6, urgency="medium", created_at=base_date + timedelta(days=8)),
        FoodRequest(student_id=1, food_category="grains", quantity_needed=8, urgency="high", created_at=base_date + timedelta(days=12)),
        FoodRequest(student_id=1, food_category="produce", quantity_needed=2, urgency="low", created_at=base_date + timedelta(days=2)),
        FoodRequest(student_id=1, food_category="produce", quantity_needed=4, urgency="medium", created_at=base_date + timedelta(days=9)),
    ]

    db.session.bulk_save_objects(demo_requests)
    db.session.commit()
    print(f"Added {len(demo_requests)} sample historical requests.")