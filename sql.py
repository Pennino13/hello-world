from cs50 import SQL
#Configure CS50 Library to use SQLite database
db = SQL("sqlite:///hints.db")


db.execute("ALTER TABLE users ADD COLUMN score INTEGER NOT NULL DEFAULT 0;")
#for i in range(1,13):
    #db.execute("ALTER TABLE hints ADD hint_? VARCHAR(60);", i)

