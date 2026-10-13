from models import FoodResource
from datetime import date

def match_resources_for_request(food_request):
    """
    Takes a FoodRequest and returns a ranked list of (resource, score) tuples,
    best match first.
    """
    available_resources = FoodResource.query.filter_by(status="available").all()
    student_location = food_request.student.location

    scored_resources = []

    for resource in available_resources:
        score = 0

        # 1. Category match matters most - no point matching rice to someone who needs dairy
        if resource.food_category == food_request.food_category:
            score += 50

        # 2. Quantity fit - reward resources that can fully cover the request
        if resource.quantity_available >= food_request.quantity_needed:
            score += 30
        else:
            coverage_ratio = resource.quantity_available / food_request.quantity_needed
            score += int(20 * coverage_ratio)

        # 3. Urgency - high urgency requests get boosted matching priority
        urgency_weights = {"high": 15, "medium": 8, "low": 3}
        score += urgency_weights.get(food_request.urgency, 0)

        # 4. Expiry proximity - prioritize using food that's expiring soon (reduces waste)
        if resource.expiry_date:
            days_until_expiry = (resource.expiry_date - date.today()).days
            if days_until_expiry <= 3:
                score += 10
            elif days_until_expiry <= 7:
                score += 5

        # 5. Location match - a donor in the same area as the student is more practical to arrange
        if resource.donor.location and student_location:
            if resource.donor.location.strip().lower() == student_location.strip().lower():
                score += 15

        scored_resources.append((resource, score))

    scored_resources.sort(key=lambda pair: pair[1], reverse=True)

    return scored_resources