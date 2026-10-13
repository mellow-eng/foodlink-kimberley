import pandas as pd
from sklearn.linear_model import LinearRegression
from models import FoodRequest

def get_demand_predictions():
    """
    For each food category, predicts the next likely request quantity
    based on historical FoodRequest data.
    """
    requests = FoodRequest.query.all()

    if not requests:
        return {}

    data = [{
        "category": r.food_category,
        "quantity": r.quantity_needed,
        "created_at": r.created_at
    } for r in requests]

    df = pd.DataFrame(data)
    df["day_number"] = (df["created_at"] - df["created_at"].min()).dt.days

    predictions = {}

    for category in df["category"].unique():
        cat_df = df[df["category"] == category]

        if len(cat_df) < 2:
            predictions[category] = {
                "predicted_next_demand": round(cat_df["quantity"].mean(), 1),
                "method": "average (need more data for a trend)",
                "data_points": len(cat_df)
            }
            continue

        X = cat_df[["day_number"]]
        y = cat_df["quantity"]

        model = LinearRegression()
        model.fit(X, y)

        next_day = cat_df["day_number"].max() + 1
        predicted = model.predict([[next_day]])[0]
        predicted = max(0, round(predicted, 1))

        predictions[category] = {
            "predicted_next_demand": predicted,
            "method": "linear trend",
            "data_points": len(cat_df)
        }

    return predictions
def evaluate_model():
    """
    Tests the model's accuracy: for each category with at least 3 requests,
    trains on all but the most recent request and checks how close the
    prediction was to what actually happened.
    """
    requests = FoodRequest.query.all()
    if not requests:
        return {}

    data = [{
        "category": r.food_category,
        "quantity": r.quantity_needed,
        "created_at": r.created_at
    } for r in requests]

    df = pd.DataFrame(data)
    df["day_number"] = (df["created_at"] - df["created_at"].min()).dt.days

    evaluation = {}

    for category in df["category"].unique():
        cat_df = df[df["category"] == category].sort_values("day_number")

        if len(cat_df) < 3:
            evaluation[category] = {
                "status": "Not enough data to evaluate (need at least 3 requests)"
            }
            continue

        train_df = cat_df.iloc[:-1]
        test_row = cat_df.iloc[-1]

        model = LinearRegression()
        model.fit(train_df[["day_number"]], train_df["quantity"])

        predicted = model.predict([[test_row["day_number"]]])[0]
        actual = test_row["quantity"]
        absolute_error = abs(predicted - actual)

        evaluation[category] = {
            "status": "evaluated",
            "actual": actual,
            "predicted": round(predicted, 1),
            "absolute_error": round(absolute_error, 1),
            "trained_on": len(train_df)
        }

    return evaluation
