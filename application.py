import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, update_is_ok, get_hints, get_card, register_password, check_unique, is_admin

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///hints.db")

# Define is_ok limit to enter play-stack for a card.
barrier = 5

@app.route("/")
@login_required
def index():
    username = db.execute("SELECT username FROM users WHERE id = ?;", session["user_id"])[0]['username']

    # Get overall score.
    score = db.execute(
        "SELECT SUM(is_ok) FROM cards WHERE user_id = ?", session["user_id"])[0]["SUM(is_ok)"]
    print(score)
    # Insert this score into users.
    if not score:
        score = 0
    db.execute(
        "UPDATE users SET scores = ? WHERE id = ?", score, session["user_id"])

    return render_template("index.html", username=username, score=score, is_admin=is_admin(db))

@app.route("/create", methods=["GET", "POST"])
@login_required
def create():
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        fields = request.form.getlist("field")
        solution = request.form.get("solution")

        category = request.form.get("category")
        language = request.form.get("language")

        if request.form.get("button") == 'draft':
            # Put to drafts ala create but different table.
            # Put in database
            db.execute(

            "INSERT INTO drafts (user_id, solution, category, language) VALUES (?, ?, ?, ?);",

            session["user_id"], solution, category, language

            )

            current_id = db.execute("SELECT MAX(id) FROM drafts WHERE user_id = ?;", session["user_id"])[0]['MAX(id)']
            # print(current_id)
            for i, x in zip(range (1,21), fields):
                db.execute(

                "UPDATE drafts SET hint_? = ? WHERE id = ?;", i, x, current_id

                )

            return redirect("/mydrafts")




        # for i in fields:
            # if i == None or i == "":
                # return redirect("must provide input to every field", 403)


        # Put in database
        db.execute(

        "INSERT INTO cards (user_id, is_ok, solution, category, language) VALUES (?, ?, ?, ?, ?);",

        session["user_id"], 0, solution, category, language

        )

        current_id = db.execute("SELECT MAX(id) FROM cards WHERE user_id = ?;", session["user_id"])[0]['MAX(id)']
        # print(current_id)
        for i, x in zip(range(1, len(fields) + 1), fields):
            db.execute(

            "UPDATE cards SET hint_? = ? WHERE id = ?;", i, x, current_id

            )

        return render_template("created.html")

    else:
        return render_template("create.html")

@app.route("/review", methods=["GET", "POST"])
@login_required
def review():
    number = 20
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Do not allow user to review his own cards.
        # if get_card(db)["user_id"] == session["user_id"]:
            # return apology("you cannot review your own cards", 403)

        # Update language
        language = request.form.get("language")
        if language != None:
            # Get unapproved cards from database
            cards = db.execute(

            "SELECT * FROM cards WHERE is_ok < ? AND user_id != ? AND language = ? ORDER BY RANDOM() LIMIT ?;",
            barrier, session["user_id"], language, number

            )

            return render_template("review.html", cards=cards)

        #if request.form.get("language")

        return render_template("review_card.html", card=get_card(db), zipped_hints=get_hints(get_card(db)), is_admin=is_admin(db))

    else:
        # Get unapproved cards from database
        cards = db.execute(

        "SELECT * FROM cards WHERE is_ok < ? AND user_id != ? ORDER BY is_ok DESC LIMIT ?;",
        barrier, session["user_id"], number

        )

        return render_template("review.html", cards=cards)

@app.route("/review_card", methods=["POST"])
@login_required
def review_card():

    # update_is_ok(db)

    if update_is_ok(db) == -1 :
            return render_template("feedback_.html", card=get_card(db))

    return redirect("/review")

@app.route("/play", methods=["GET", "POST"])
def play():
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        #update_is_ok(db)

        if update_is_ok(db) == -1 :
            return render_template("feedback_.html", card=get_card(db))

        if request.form.get("language") == 'Deutsch':
            return redirect("/play_de")

        return redirect("/play")

    else:
        # Get random card, that is approved.
        card = db.execute(
            "SELECT * from cards WHERE is_ok >= ? AND language = 'English' ORDER BY RANDOM() LIMIT 1;", barrier
            )[0]
        print(card)

        return render_template("play.html", card=card, zipped_hints=get_hints(card), is_admin=is_admin(db))

@app.route("/play_de", methods=["GET"])
def play_de():

    # Get random card, that is approved.
    card = db.execute(
        "SELECT * from cards WHERE is_ok >= ? AND language == 'Deutsch' OR language == 'GER' ORDER BY RANDOM() LIMIT 1;", barrier
        )[0]

    return render_template("play.html", card=card, zipped_hints=get_hints(card), is_admin=is_admin(db))

@app.route("/my", methods=["GET", "POST"])
@login_required
def my():
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Let user edit his card.

        # Cards with is_ok > 5 are not allowed to be edited
        # if get_card(db)["is_ok"] > 5:
            # return apology("Cards in Play-Stack cannot be edited", 403)

        # Check if messages and post them.
        messages = db.execute(
        "SELECT id, message from feedbacks WHERE card_id == ?",
        get_card(db)["id"]
        )
        # Only if there is a message
        if bool(messages) != False:
            return render_template("my_edit.html", card=get_card(db), zipped_hints=get_hints(get_card(db)), table='cards', messages=messages)


        return render_template("my_edit.html", card=get_card(db), zipped_hints=get_hints(get_card(db)), table='cards')

    else:
        # Populate (my) cards list
        cards = db.execute(

        "SELECT * from cards WHERE user_id = ?;",

        session["user_id"]

        )

        # bool list, check if message
        bool_list = []
        messages = {}
        counter = 0
        # Get messages
        for i in cards:

            messages[counter] = db.execute(

            "SELECT message from feedbacks WHERE card_id = ?;",

            i["id"]

            )
            print(messages[counter])

            if len(messages[counter]) == 0:
                bool_list.append(False)
            else:
                bool_list.append(True)
            counter += 1

        print(bool_list)
        cards_zip = zip(range(0, len(cards)), cards)
        return render_template("my.html", cards_zip=cards_zip, bool_list=bool_list)

@app.route("/my_edit", methods=["POST"])
@login_required
def my_edit():

    # If advide should be deleted, just delete advice redirect my cards.
    if request.form.get("button") == 'advice':
        feedback_id = request.form.get("feedback_id")
        print(feedback_id)
        db.execute(
        "DELETE FROM feedbacks WHERE id = ?",
        feedback_id
        )

        return redirect("/my")


    # Get card that is to be edited
    table = request.form.get("table")
    card = get_card(db, table)

    fields = request.form.getlist("field")
    current_id = card["id"]
    solution = request.form.get("solution")
    language = request.form.get("language")
    category = request.form.get("category")

    # !!! Handle case, that LANG AND CATEGORY ARE UPDATED!!!
    if request.form.get("button") == 'delete':
        db.execute(

            "DELETE from drafts WHERE id = ?;",
            current_id

            )
        return redirect("/mydrafts")
    # Check if a draft now wants to be a card.
    elif request.form.get("button") == 'create':
        # Insert into cards ala create
        for i in fields:
            if i == None or i == "":
                return apology("must provide input to every field", 403)


        # Put in database
        db.execute(

        "INSERT INTO cards (user_id, is_ok, solution, category, language) VALUES (?, ?, ?, ?, ?);",

        session["user_id"], 0, solution, category, language

        )

        post_id = db.execute("SELECT MAX(id) FROM cards WHERE user_id = ?;", session["user_id"])[0]['MAX(id)']
        # print(current_id)
        for i, x in zip(range (1,len(fields)+ 1), fields):
            db.execute(

            "UPDATE cards SET hint_? = ? WHERE id = ?;", i, x, post_id

            )

        # Delete from drafts
        #TODO
        db.execute(

            "DELETE from drafts WHERE id = ?;",
            current_id

            )

        return redirect("/my")

    elif request.form.get("button") == 'into_draft':
        # Copy to drafts and delete from cards
        # Put in database drafts
        db.execute(

        "INSERT INTO drafts (user_id, solution, category, language) VALUES (?, ?, ?, ?);",

        session["user_id"], solution, category, language

        )

        post_id = db.execute("SELECT MAX(id) FROM drafts WHERE user_id = ?;", session["user_id"])[0]['MAX(id)']
        # print(current_id)
        for i, x in zip(range (1,21), fields):
            db.execute(

            "UPDATE drafts SET hint_? = ? WHERE id = ?;", i, x, post_id

            )

        # Delete from cards
        db.execute(

            "DELETE from cards WHERE id = ?;",
            current_id

            )
        return redirect("mydrafts")



    else:
        # Edit this card accordingly.
        # Update solution
        db.execute(

                "UPDATE ? SET (solution, language, category) = (?, ?, ?) WHERE id = ?;", table, solution, language, category, current_id

                )
        # Update hint fields
        for i, x in zip(range (1,21), fields):
                db.execute(

                "UPDATE ? SET hint_? = ? WHERE id = ?;", table, i, x, current_id

                )
        if table == 'cards':
            return redirect("/my")
        else:
            return redirect("mydrafts")


@app.route("/mydrafts", methods=["GET", "POST"])
@login_required
def mydrafts():
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Let user edit his card.

        return render_template("my_edit.html", card=get_card(db, 'drafts'), zipped_hints=get_hints(get_card(db, 'drafts')), table='drafts')

    else:
        # Populate (my) cards list
        cards = db.execute(

        "SELECT * from drafts WHERE user_id = ?;",

        session["user_id"]

        )

        return render_template("mydrafts.html", cards=cards)

@app.route("/feedback_", methods=["POST"])
@login_required
def feedback_():
    option = request.form.get("button")

    if option == 'review':
        return redirect("/review")
    elif option == 'play':
        if request.form.get("language") == 'Deutsch':
            return redirect("/play_de")
        return redirect("/play")
    else:
        return render_template("give_feedback.html", card=get_card(db), zipped_hints=get_hints(get_card(db)))

@app.route("/give_feedback", methods=["POST"])
@login_required
def give_feedback():
    message = request.form.get("message")
    card = get_card(db)

    # Put message into feedbacks table.
    db.execute(
    "INSERT INTO feedbacks (card_id, message) VALUES (?, ?);",
    card["id"], message
    )

    return render_template("created.html")


@app.route("/about", methods=["GET"])
def about():
    return render_template("about.html")

@app.route("/ranking", methods=["GET"])
@login_required
def ranking():
    ranks = 12;
    top_users = db.execute(
        "SELECT username, scores FROM users ORDER BY scores DESC LIMIT ?", ranks)

    top_usernames = []
    top_scores = []
    for i in top_users:
        top_usernames.append(i["username"])
        top_scores.append(i["scores"])

    zipped_tops = zip(range(1, ranks + 1), top_usernames, top_scores)

    return render_template("ranking.html", zipped_tops=zipped_tops)

@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    if request.method == "POST":
        # Do sth. to users table depending on which button: Change username and/or password or Delete user
        # Change username
        if request.form.get("form_username") == "0":
            # Ensure unique username
            username = request.form.get("new_username")
            if check_unique(db, username) == 1:
                return apology("username already exists", 403)

            db.execute(
                "UPDATE users SET username = ? WHERE id = ?",
                username, session["user_id"])
        else:
            # Query database for username
            rows = db.execute("SELECT * FROM users WHERE id = ?",
                          session["user_id"])

            # Check if current password match
            if not check_password_hash(rows[0]["hash"], request.form.get("old_password")):
                return apology("current password was not correct", 403)

            if register_password() != 0:
                return apology("provide password and confirmation", 403)

            # INSERT the new user into users
            db.execute("UPDATE users SET hash = ? WHERE id = ?", generate_password_hash(request.form.get("password")), session["user_id"])

        # Redirect user to home page
        return redirect("/")

    else:
        # Show the settings.html site
        # Get username

        username = db.execute(
                "SELECT username FROM users WHERE id = ?",
                session["user_id"]
                )[0]["username"]

        return render_template("settings.html", user_id=session["user_id"], username=username)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        username = request.form.get("username")
        # Ensure username was submitted
        if not username:
            return apology("must provide username", 403)

        # Ensure unique username
        if check_unique(db, username) == 1:
            return apology("username already exists", 403)

        if register_password() != 0:
            return apology("provide password and confirmation", 403)

        # INSERT the new user into users
        db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", request.form.get("username"), generate_password_hash(request.form.get("password")))

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

# Guideline for good cards.
@app.route("/create_guideline", methods=["GET"])
@login_required
def create_guideline():
    return render_template("create_guideline.html")
