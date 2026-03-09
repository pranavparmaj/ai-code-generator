from flask import request

def register_user():

    username = request.form.get("username")
    password = request.form.get("password")

    # Insert user into database

    return "User registered successfully"