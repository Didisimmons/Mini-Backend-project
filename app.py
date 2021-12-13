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
        return redirect(url_for("profile", username=session["user"]))
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
            return redirect(url_for("login"))

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


@app.route("/add_task", methods=["GET", "POST"])
def add_task():
    if request.method == "POST":
        """create our own dictionary of items from the form, stored in a variable
        called 'task'.Inside of this dictionary, we set our key-value pairs 
        using our name attributes from the form"""
        """ Create a new variable, which will also be called 'is_urgent'.
        That will be set to 'on' if our requested form element for 'is_urgent' is truthy.
        Otherwise, or else, it will be set to 'off' by default"""
        is_urgent = "on" if request.form.get("is_urgent") else "off"
        task = {
            "category_name": request.form.get("category_name"),
            "task_name":request.form.get("task_name"),
            "task_description":request.form.get("task_description"),
            "is_urgent": is_urgent,
            "due_date":request.form.get("due_date"),
            "created_by": session["user"] #This will grab the username of the person adding the new task, and insert it here
        }
        mongo.db.tasks.insert_one(task)
        flash("Task Sucessfully Added!")
        return redirect(url_for("get_tasks"))

    """ our Categories collection on MongoDB would dynamically
    generate an <option> instance for each category in our collection
    The categories will display in the same order we added them to the database, so let's sort
    them by the category_name key, using 1 for ascending, or alphabetical."""
    categories = mongo.db.categories.find().sort("category_name", 1)
    return render_template("add_task.html", categories=categories)
    #This function will pretty much do the same thing as our GET method on the 'add_task'function above


@app.route("/edit_task/<task_id>", methods=["GET", "POST"])
def edit_task(task_id):
    """The POST functionality for editing a task is quite similar to adding a task"""
    if request.method == "POST":
        is_urgent = "on" if request.form.get("is_urgent") else "off"
        submit = {
            "category_name": request.form.get("category_name"),
            "task_name": request.form.get("task_name"),
            "task_description": request.form.get("task_description"),
            "is_urgent": is_urgent,
            "due_date": request.form.get("due_date"),
            "created_by": session["user"]
        }
        """ We need to rename the above dictionary variable one so we don't have duplicate 
        variable names, that is updated in to MongoDB as well.This time, we're not inserting_one,
        but instead, we're going to use the .update() method.This method takes two parameters, 
        both of which are dictionaries.the second one already is the dictionary of our submitted
        items from the form. The first one needs to specify which task we're going to update, 
        and we'll target that by using the ObjectID.The task_id is being passed through our route,
        so we can have it search based on that ID.
        To recap, we're going to search for a task in the database by the task ID coming from
        the route """
        mongo.db.tasks.update_one({"_id": ObjectId(task_id)}, {"$set": submit})
        flash("Task Successfully Updated")

    """First, we need to retrieve the task from the database that we are wanting to edit.
    A guaranteed way of targeting the correct task, is to use its ID, similar to a primary
    key in a relational database"""
    """The ID needs to be converted into a BSON data-type, which is a readable format that's acceptable
    by MongoDB.This is the 'task_id' that we want to search within the database, which is going to be
    passed through into our URL """
    task = mongo.db.tasks.find_one({"_id": ObjectId(task_id)})
    categories = mongo.db.categories.find().sort("category_name", 1)
    return render_template("edit_task.html", task=task, categories=categories)


@app.route("/delete_task/<task_id>")
def delete_task(task_id):
    """Similar to how we retrieve or edit a task, we need to get the specific task by the ObjectId
    that matches the 'task_id' variable """
    mongo.db.tasks.delete_one({"_id": ObjectId(task_id)})
    flash("Task successfully deleted")
    return redirect(url_for("get_tasks"))
    


@app.route("/get_categories")
def get_categories():
    """We're also going to convert it to a proper list, and then sort them alphabetically by
    the category_name """
    categories = list(mongo.db.categories.find().sort("category_name", 1))
    """the first 'categories' is what gets passed into our template(name of html file)
    The second 'categories' is the variable defined above, what's actually being returned from
    the database"""
    return render_template("categories.html", categories=categories)


@app.route("/add_category", methods=["GET", "POST"])
def add_category():
    if request.method == "POST":
        category = {
            "category_name": request.form.get("category_name"),
        }
        mongo.db.categories.insert_one(category)
        flash("New Category Added")
        return redirect(url_for("get_categories"))

    return render_template("add_category.html")


@app.route("/edit_category/<category_id>", methods=["GET", "POST"])
def edit_category(category_id):
    """Our form only has the one item, 'category_name', which we'll get from the requested form itself"""
    if request.method == "POST":
        submit = {
            "category_name": request.form.get("category_name"),
        }
        """The second one is our 'submit' dictionary, so it knows what new information will be updated
        in the database.The first dictionary will define which specific category we want to update"""
        mongo.db.categories.update_one({"_id": ObjectId(category_id)}, {"$set": submit})
        flash("Category Sucessfully Updated")
        return redirect(url_for("get_categories"))

    """using the ObjectID, this will render as BSON in order to properly display
    between MongoDB and Flask"""
    category = mongo.db.categories.find_one({"_id": ObjectId(category_id)})
    """Our template is expecting a variable called 'category', so that we can specify which category
    is being updated on the form.set that equal to the new category variable found above"""
    return render_template("edit_category.html", category=category)

if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
        port=int(os.environ.get("PORT")),
        debug=True)

