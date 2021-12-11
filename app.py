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
    tasks = list(mongo.db.tasks.find())
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
        """let's redirect them to our new profile template.
        Our profile template is looking for the variable of 'username' if you recall, so we need to
        set that equal to the same session cookie of 'user' """
        return redirect(url_for("profile",username=session["user"]))
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
                    flash("Welcome, {}".format(
                        request.form.get("username")))#the format will be our requested form elementfor 'username'.
                    return redirect(url_for(
                        "profile",username=session["user"]))
            else:
                #invalid password match
                flash("Incorrect Username and/or Password")
                return redirect (url_for("login"))
        
        else:
            #username does not exist 
            flash("Incorrect Username and/or Password")
            return redirect (url_for("login"))

    return render_template("login.html")


@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    # create a new variable called 'username', and that will be the user that we find from the database, but this time, we'll use our session variable of 'user'.
    #grab the session user's username from the database     
    """ we want to retrieve just the username stored, so at the end, let's include more
    square-brackets to specify that we only want to grab the 'username' key field from this
    record """
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]

    """If our session['user'] cookie is truthy, then we want to return the appropriate profile
    template so that users can't just force the URL to someone else's profile"""
    if session["user"]:
        #The first 'username' is what the template is expecting to retrieve on the HTML file.
        # The second 'username' is what we've defined on the line above.
        return render_template("profile.html", username=username) 
    
    """ However, if it's not true or doesn't exist, we'll return the user back to the login template
    instead """
    return redirect(url_for("login"))

@app.route("/logout")
def logout():
    #remove user from session cookies
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=(os.environ.get("PORT")),
            debug=True)
