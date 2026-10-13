from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, current_user, logout_user
from extensions import db, login_manager
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key-change-later'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///foodlink.db'

db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login'

from models import Student, Donor, FoodRequest, FoodResource

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("is_admin"):
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated

@login_manager.user_loader
def load_user(user_id):
    user_type, actual_id = user_id.split("-")
    if user_type == "student":
        return Student.query.get(int(actual_id))
    elif user_type == "donor":
        return Donor.query.get(int(actual_id))
    return None

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        new_student = Student(
            full_name=request.form["full_name"],
            email=request.form["email"],
            password_hash=generate_password_hash(request.form["password"]),
            location=request.form["location"]
        )
        db.session.add(new_student)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return render_template("register.html", error="That email is already registered. Try logging in instead.")

        login_user(new_student)
        return redirect(url_for('dashboard'))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        student = Student.query.filter_by(email=email).first()

        if student and check_password_hash(student.password_hash, password):
            login_user(student)
            return redirect(url_for('dashboard'))

        return render_template("login.html", error="Invalid email or password. Try again.")

    return render_template("login.html")

@app.route("/donor/register", methods=["GET", "POST"])
def donor_register():
    if request.method == "POST":
        new_donor = Donor(
            name=request.form["name"],
            email=request.form["email"],
            password_hash=generate_password_hash(request.form["password"]),
            location=request.form["location"]
        )
        db.session.add(new_donor)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return render_template("donor_register.html", error="That email is already registered. Try logging in instead.")

        login_user(new_donor)
        return redirect(url_for('donor_dashboard'))

    return render_template("donor_register.html")

@app.route("/donor/login", methods=["GET", "POST"])
def donor_login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        donor = Donor.query.filter_by(email=email).first()

        if donor and check_password_hash(donor.password_hash, password):
            login_user(donor)
            return redirect(url_for('donor_dashboard'))

        return render_template("donor_login.html", error="Invalid email or password. Try again.")

    return render_template("donor_login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route("/dashboard")
@login_required
def dashboard():
    my_requests = FoodRequest.query.filter_by(student_id=current_user.id).all()
    return render_template("dashboard.html", my_requests=my_requests)

@app.route("/donor/dashboard")
@login_required
def donor_dashboard():
    my_resources = FoodResource.query.filter_by(donor_id=current_user.id).all()
    return render_template("donor_dashboard.html", my_resources=my_resources)

@app.route("/request/new", methods=["GET", "POST"])
@login_required
def submit_request():
    if request.method == "POST":
        new_request = FoodRequest(
            student_id=current_user.id,
            food_category=request.form["food_category"],
            quantity_needed=int(request.form["quantity_needed"]),
            urgency=request.form["urgency"]
        )
        db.session.add(new_request)
        db.session.commit()
        return redirect(url_for('dashboard'))

    return render_template("submit_request.html")

@app.route("/resource/new", methods=["GET", "POST"])
@login_required
def submit_resource():
    if request.method == "POST":
        from datetime import datetime
        expiry_str = request.form["expiry_date"]
        expiry = datetime.strptime(expiry_str, "%Y-%m-%d").date() if expiry_str else None

        new_resource = FoodResource(
            donor_id=current_user.id,
            food_category=request.form["food_category"],
            quantity_available=int(request.form["quantity_available"]),
            expiry_date=expiry
        )
        db.session.add(new_resource)
        db.session.commit()
        return redirect(url_for('donor_dashboard'))

    return render_template("submit_resource.html")

@app.route("/request/<int:request_id>/matches")
@login_required
def view_matches(request_id):
    food_request = FoodRequest.query.get_or_404(request_id)

    from services import match_resources_for_request
    matches = match_resources_for_request(food_request)

    return render_template("matches.html", food_request=food_request, matches=matches)

@app.route("/demand-forecast")
@login_required
def demand_forecast():
    from demand_prediction import get_demand_predictions, evaluate_model
    predictions = get_demand_predictions()
    evaluation = evaluate_model()
    return render_template("demand_forecast.html", predictions=predictions, evaluation=evaluation)

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if request.form["username"] == ADMIN_USERNAME and request.form["password"] == ADMIN_PASSWORD:
            session["is_admin"] = True
            return redirect(url_for("admin_dashboard"))
        return render_template("admin_login.html", error="Invalid admin credentials")
    return render_template("admin_login.html")

@app.route("/admin/logout")
def admin_logout():
    session.pop("is_admin", None)
    return redirect(url_for("admin_login"))

@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    from demand_prediction import get_demand_predictions

    student_count = Student.query.count()
    donor_count = Donor.query.count()
    pending_count = FoodRequest.query.filter_by(status="pending").count()
    available_count = FoodResource.query.filter_by(status="available").count()
    completed_count = FoodRequest.query.filter_by(status="fulfilled").count()

    predictions = get_demand_predictions()
    next_day_total = round(sum(p["predicted_next_demand"] for p in predictions.values())) if predictions else 0

    if next_day_total < 5:
        overall_level = "Low"
    elif next_day_total < 15:
        overall_level = "Medium"
    else:
        overall_level = "High"

    pending_requests = FoodRequest.query.filter_by(status="pending").join(Student).all()
    location_data = {}
    for r in pending_requests:
        loc = r.student.location
        location_data[loc] = location_data.get(loc, 0) + 1

    location_summary = []
    for loc, count in location_data.items():
        if count < 3:
            level = "Low"
        elif count < 7:
            level = "Medium"
        else:
            level = "High"
        location_summary.append({"location": loc, "count": count, "level": level})

    return render_template(
        "admin_dashboard.html",
        student_count=student_count,
        donor_count=donor_count,
        pending_count=pending_count,
        available_count=available_count,
        completed_count=completed_count,
        next_day_total=next_day_total,
        overall_level=overall_level,
        location_summary=location_summary
    )

@app.route("/admin/users")
@admin_required
def admin_users():
    students = Student.query.all()
    donors = Donor.query.all()
    return render_template("admin_users.html", students=students, donors=donors)

@app.route("/admin/requests")
@admin_required
def admin_requests():
    requests = FoodRequest.query.all()
    return render_template("admin_requests.html", requests=requests)

@app.route("/admin/donations")
@admin_required
def admin_donations():
    resources = FoodResource.query.all()
    return render_template("admin_donations.html", resources=resources)

@app.route("/admin/requests/<int:request_id>/fulfill", methods=["POST"])
@admin_required
def admin_fulfill_request(request_id):
    food_request = FoodRequest.query.get_or_404(request_id)
    food_request.status = "fulfilled"
    db.session.commit()
    return redirect(url_for("admin_requests"))

@app.route("/admin/donations/<int:resource_id>/give", methods=["POST"])
@admin_required
def admin_give_resource(resource_id):
    resource = FoodResource.query.get_or_404(resource_id)
    resource.status = "given"
    db.session.commit()
    return redirect(url_for("admin_donations"))

if __name__ == "__main__":
    app.run(debug=True)

    