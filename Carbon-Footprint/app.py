from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
import hashlib
import pandas as pd
import numpy as np
import pickle
from functions import *
import matplotlib
matplotlib.use('Agg')
app = Flask(__name__)
app.secret_key = "carbon_secret"

# Load ML model
model = pickle.load(open("models/model.sav","rb"))
scaler = pickle.load(open("models/scale.sav","rb"))

# ---------------- DATABASE ----------------

def create_db():
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT
    )
    """)

    conn.commit()
    conn.close()

create_db()

# ---------------- LOGIN PAGE ----------------

@app.route("/")
def login():
    return render_template("login.html")


# ---------------- REGISTER ----------------

@app.route("/register", methods=["GET","POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = hashlib.sha256(request.form["password"].encode()).hexdigest()

        conn = sqlite3.connect("users.db")
        cur = conn.cursor()

        try:
            cur.execute("INSERT INTO users(name,email,password) VALUES(?,?,?)",
                        (name,email,password))
            conn.commit()
        except:
            return "User already exists"

        conn.close()

        return redirect("/")

    return render_template("register.html")


# ---------------- LOGIN CHECK ----------------

@app.route("/login", methods=["POST"])
def login_user():

    email = request.form["email"]
    password = hashlib.sha256(request.form["password"].encode()).hexdigest()

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    cur.execute("SELECT * FROM users WHERE email=? AND password=?",(email,password))
    user = cur.fetchone()

    conn.close()

    if user:
        session["user"] = user[1]
        return redirect("/home")
    else:
        return "Invalid Login"


# ---------------- HOME PAGE ----------------

@app.route("/home")
def home():

    if "user" not in session:
        return redirect("/")

    return render_template("index.html",name=session["user"])


# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():
    session.pop("user",None)
    return redirect("/")


# ---------------- PREDICTION ----------------

@app.route("/predict", methods=["POST"])
def predict():

    height = 165
    weight = 60

    bmi = weight/(height/100)**2

    if bmi < 18.5:
        body_type = "underweight"
    elif bmi < 25:
        body_type = "normal"
    elif bmi < 30:
        body_type = "overweight"
    else:
        body_type = "obese"

    data = {
        'Body Type': body_type,
        'Sex': 'male',
        'Diet': 'vegetarian',
        'How Often Shower': 'more frequently',
        'Heating Energy Source': 'electricity',
        'Transport': request.form["transport"],
        'Social Activity': request.form["social"],
        'Monthly Grocery Bill': 5000,
        'Frequency of Traveling by Air': request.form["air"],
        'Vehicle Monthly Distance Km': int(request.form["distance"]),
        'Waste Bag Size': request.form["waste_size"],
        'Waste Bag Weekly Count': int(request.form["waste_count"]),
        'How Long TV PC Daily Hour': int(request.form["tv"]),
        'Vehicle Type': request.form["vehicle"],
        'How Many New Clothes Monthly': 2,
        'How Long Internet Daily Hour': int(request.form["internet"]),
        'Energy efficiency': request.form["energy"]
    }

    df = pd.DataFrame(data,index=[0])

    processed = input_preprocessing(df)

    sample_df = pd.DataFrame(data=sample,index=[0])
    sample_df[sample_df.columns] = 0
    sample_df[processed.columns] = processed

    prediction = round(np.exp(model.predict(scaler.transform(sample_df))[0]))

    trees = round(prediction / 411.4)

    return render_template("result.html",prediction=prediction,trees=trees)


import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)