from flask import request, redirect, session

def login_user():

    username = request.form.get("username")
    password = request.form.get("password")

    # Validate user credentials
    # Query database

    if username == "admin":
        session["user"] = username
        return redirect("/dashboard")

    return "Invalid credentials"