import os
from flask import (
    Flask, flash, render_template,
    redirect, request, url_for, session)  
from flask_pymongo import PyMongo 
from bson.objectid import ObjectId #In order to find documents from MongoDB
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
#generate data from our tasks collection
def get_tasks():
    tasks = mongo.db.tasks.find()
    return render_template("tasks.html" , tasks=tasks)


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=(os.environ.get("PORT")),
            debug=True)
