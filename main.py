import datetime
import os

from flask import Flask, render_template, request, url_for, redirect, flash
from flask_wtf import FlaskForm
from sqlalchemy import create_engine, text
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from wtforms import StringField, SubmitField, PasswordField, FloatField, DateField
from wtforms.validators import DataRequired
from flask_bootstrap import Bootstrap
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
import pandas as pd
import matplotlib.pyplot as plt
from sqlalchemy.orm import relationship



app = Flask(__name__)
Bootstrap(app)
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///workoutHub.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)


# cnx = create_engine('sqlite:///workoutHub.db').connect()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))

    exercises = relationship("Workout", back_populates="author")


class Workout(db.Model):
    __tablename__ = 'workouts'
    id = db.Column(db.Integer, primary_key=True)

    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    author = relationship("User", back_populates="exercises")

    date = db.Column(db.DateTime())
    workout = db.Column(db.String(100))
    sets = db.Column(db.Integer)
    reps = db.Column(db.Integer)
    kgs = db.Column(db.Integer)




# with app.app_context():
#     db.create_all()


class RegisterForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Submit")


# form class for login
class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Submit")


# Form for Weights
class WeightsForm(FlaskForm):
    date = DateField('Date')
    sets = StringField("Number of sets", validators=[DataRequired()])
    reps = StringField("Number of reps per set", validators=[DataRequired()])
    kgs = FloatField("What weight did you use", validators=[DataRequired()])
    submit = SubmitField("Submit")

class AddNew(FlaskForm):
    exercise = StringField("Name of exercise/workout", validators=[DataRequired()])
    date = DateField('Date')
    sets = StringField("Number of sets", validators=[DataRequired()])
    reps = StringField("Number of reps per set", validators=[DataRequired()])
    kgs = FloatField("What weight did you use", validators=[DataRequired()])
    submit = SubmitField("Submit")


# workouts = []
# with app.app_context():
#     for workout in Workout.query.with_entities(Workout.workout).distinct().all():
#         workouts.append(workout.workout)


@app.route('/home', methods=['GET', 'POST'])
@login_required
def home():
    # Workout.query.with_entities(Workout.workout).distinct().all():
    workouts = []
    with app.app_context():
        more_workouts = Workout.query.join(User).filter(User.id == current_user.id).all()
        for workout in more_workouts:
            workouts.append(workout.workout)
    return render_template("home.html", workouts=workouts, current_user=current_user)


@app.route('/add', methods=['GET', 'POST'])
def add():
    form = AddNew()
    if form.validate_on_submit():
        new_workout = Workout(
            date=form.date.data,
            workout=form.exercise.data.title(),
            sets=form.sets.data,
            reps=form.reps.data,
            kgs=form.kgs.data,
            author_id=current_user.id
        )
        with app.app_context():
            db.session.add(new_workout)
            db.session.commit()
            return redirect(url_for('home'))

    return render_template("addNew.html", form=form, current_user=current_user)


@app.route('/register', methods=["POST", "GET"])
def register():
    form = RegisterForm()
    if request.method == "POST":
        hashed_password = generate_password_hash(password=form.password.data,
                                                 method='pbkdf2:sha256',
                                                 salt_length=8)

        new_user = User(
            name=form.name.data,
            email=form.email.data,
            password=hashed_password

        )
        with app.app_context():
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('login'))





    return render_template("register.html", form=form)


@app.route('/', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        print(email, password)

        user = User.query.filter_by(email=email).first()
        if not user:
            flash("Email does not exist, try again!")
            return redirect(url_for('login'))

        elif not check_password_hash(user.password, password):
            flash("Wrong Password!!")
            return redirect(url_for('login'))

        else:
            login_user(user)
            return redirect(url_for('home'))


    return render_template("login.html", form=form)




@app.route('/workout/<string:exercise>', methods=['GET', 'POST'])
def weights(exercise):
    form = WeightsForm()
    workout = exercise
    # workout_df = pd.read_sql("workouts", con= app.config['SQLALCHEMY_DATABASE_URI'] )
    # workout_df = pd.DataFrame(db.engine.connect().execute(text("workouts")))
    # workout_df = pd.DataFrame()
    # print(workout_df)
    if form.validate_on_submit():

        new_workout = Workout(
            date=form.date.data,
            workout=exercise,
            sets=form.sets.data,
            reps=form.reps.data,
            kgs=form.kgs.data,
            author_id=current_user.id
        )
        with app.app_context():
            db.session.add(new_workout)
            db.session.commit()
            return redirect(url_for('home'))

    return render_template("weightsBase.html", form=form, current_user=current_user, exercise=workout)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))


if __name__ == "__main__":
    app.run(debug=True)
