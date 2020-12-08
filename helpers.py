import os
import requests
import urllib.parse
from cs50 import SQL

from flask import redirect, render_template, request, session
from functools import wraps


def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def update_is_ok(db):
    card_id = request.form.get("card")
    if request.form.get("vote") == "OK":
        # Upvote is_ok in table cards
        db.execute(
        "UPDATE cards SET is_ok = is_ok + 1 WHERE id == ?",
        card_id
        )
        return 1
    else:
        # Downvote is_ok in table cards
        db.execute(
        "UPDATE cards SET is_ok = is_ok - 1 WHERE id == ?",
        card_id
        )
        return -1

def get_hints(card):
    hint_keys = []

    for key in card:
       if key.startswith('hint_'):
          hint_keys.append(key)

    hints = []

    for key in hint_keys:
        hints.append(card[key])

    # print(hints)

    zipped_hints = zip(range(1, len(hints)+1), hints)

    return zipped_hints

def get_card(db, table='cards'):
    # Get the card the user wants to review
    card_id = request.form.get("card")
    print(card_id)

    card = db.execute(

    "SELECT * FROM ? WHERE id == ?;",
    table,
    card_id

    )[0]

    return card

def register_password():
    #print(request.form.get("password"))
    #print(request.form.get("confirmation"))

    # Ensure password was submitted
    if not request.form.get("password"):
        return 1

    # Ensure password was confirmed
    if request.form.get("password") != request.form.get("confirmation"):
        return 2

    return 0

def check_unique(db, username):
    x = db.execute("SELECT * FROM users WHERE username = ?", username)
    if bool(x) == False:
        return 0
    else:
        return 1

def is_admin(db):
    query = db.execute("SELECT * FROM admins WHERE user_id = ?", session["user_id"])
    if bool(query) == True:
        return True
    else:
        return False
