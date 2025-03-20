from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import time

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'hemmelignøkkel'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

class Leaderboard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False)
    score = db.Column(db.Integer, nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = bcrypt.generate_password_hash(request.form["password"]).decode("utf-8")
        if User.query.filter_by(username=username).first():
            flash("Brukernavn er allerede tatt!", "danger")
            return redirect(url_for("register"))
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash("Registrering vellykket! Logg inn nå.", "success")
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            session["score"] = 0
            session["question_index"] = 0
            flash("Innlogging vellykket!", "success")
            return redirect(url_for("choose_category"))
        flash("Feil brukernavn eller passord", "danger")
    return render_template("login.html")

questions = {
    "Geografi": [
        {"question": "Hva er hovedstaden i Norge?", "options": ["Oslo", "Bergen", "Trondheim"], "answer": "Oslo", "image": "oslo.jpg"},
        {"question": "Hvor mange kontinenter finnes det?", "options": ["5", "6", "7"], "answer": "7", "image": ""},
    ],
    "Dyr": [
        {"question": "Hvilket dyr er kjent som 'Kongen av jungelen'?", "options": ["Løve", "Tiger", "Elefant"], "answer": "Løve", "image": "lion.jpg"},
        {"question": "Hva heter Norges nasjonalfugl?", "options": ["Kongeørn", "Fossekall", "Ravn"], "answer": "Fossekall", "image": ""},
    ],
}

@app.route("/choose_category")
@login_required
def choose_category():
    return render_template("choose_category.html", categories=questions.keys())

@app.route("/quiz/<category>", methods=["GET", "POST"])
@login_required
def quiz(category):
    if category not in questions:
        flash("Ugyldig kategori!", "danger")
        return redirect(url_for("choose_category"))

    if "question_index" not in session or session.get("category") != category:
        session["question_index"] = 0
        session["score"] = 0
        session["category"] = category
        session["start_time"] = time.time()

    index = session["question_index"]
    quiz_questions = questions[category]

    if index >= len(quiz_questions):
        final_score = session["score"]
        new_entry = Leaderboard(username=current_user.username, score=final_score)
        db.session.add(new_entry)
        db.session.commit()
        session.pop("question_index", None)
        session.pop("score", None)
        return render_template("quiz_result.html", score=final_score, total=len(quiz_questions))

    question = quiz_questions[index]
    feedback = session.pop("feedback", None)

    if request.method == "POST":
        if time.time() - session["start_time"] <0:
            session["feedback"] = "Tiden gikk ut! 😢"
        else:
            selected_answer = request.form["answer"]
            if selected_answer == question["answer"]:
                session["score"] += 1
                session["feedback"] = "Riktig! ✅"
            else:
                session["feedback"] = f"Feil! ❌ Riktig svar var {question['answer']}."

        session["question_index"] += 1
        session["start_time"] = time.time()
        return redirect(url_for("quiz", category=category))

    return render_template("quiz.html", question=question, index=index + 1, total=len(quiz_questions), category=category, feedback=feedback)

@app.route("/leaderboard")
def leaderboard():
    scores = Leaderboard.query.order_by(Leaderboard.score.desc()).limit(10).all()
    return render_template("leaderboard.html", scores=scores)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    session.pop("question_index", None)
    session.pop("score", None)
    flash("Du er logget ut.", "info")
    return redirect(url_for("home"))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
