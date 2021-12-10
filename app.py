import os
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env

app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

""" instance setup for  PyMongo using a constructor method, ensures Flask app is properly communicating with the Mongo database"""
mongo = PyMongo(app)

@app.route("/")
@app.route("/get_tasks")
def get_tasks():
    tasks = mongo.db.tasks.find()
    return render_template("tasks.html", tasks=tasks)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        #check if username already exists in db if the Mongo username field matches that of the input-field in the form
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            flash("username already exists")
            return redirect(url_for("register"))#redirect the user back to the 'register' function,so that they can try again with another username

        #if no user is found
        register = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password"))#If you were to include a secondary password field to confirm the user's password, you would want to do that prior to building this dictionary here
        }
        mongo.db.users.insert_one(register)

        #put the new user into 'session' temporary cookie and store data in mongoDB
        session["user"] = request.form.get("username").lower()#The session key in square-brackets can be whatever we'd like to call it
        flash("Registration Successful!")  
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
     if request.method == "POST":
        #check if username already exists in db if the Mongo username field matches that of the input-field in the form
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            #ensure that the hashed password matches what the user has input
            if check_password_hash(
                existing_user["password"], request.form.get("password")):
                    session["user"] = request.form.get("username").lower()#The session key in square-brackets can be whatever but its consistent for this project
                    flash("Welcome, {}".format(request.form.get("username")))#and the format will be our requested form elementfor 'username'.
            else:
                #invalid password match
                flash("Incorrect Username and/or Password")
                return redirect (url_for("login"))
        
        else:
            #username does not exist 
            flash("Incorrect Username and/or Password")
            return redirect (url_for("login"))

     return render_template("login.html")


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=(os.environ.get("PORT")),
            debug=True)
