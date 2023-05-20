import auth
import sqlite3

conn = sqlite3.connect("userdata.db")
cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS userdata (
    id INTEGER PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    fullname VARCHAR(255) NOT NULL
)
""")

un1 = "kgocmen"
pass1 = auth.hash("87654321")
em1 = "kaan@mp.com"
fn1 = "Kaan Gocmen"
un2 = "bakcm"
pass2 = auth.hash("12345678")
em2 = "baris@mp.com"
fn2 = "Baris Akcam"

cur.execute("INSERT INTO userdata (username, password, email, fullname) VALUES (? , ?, ?, ?)", (un1,pass1,em1,fn1))
cur.execute("INSERT INTO userdata (username, password, email, fullname) VALUES (? , ?, ?, ?)", (un2,pass2,em2,fn2))
delete_query1 = "DELETE FROM userdata WHERE id > 2"
cur.execute(delete_query1)
conn.commit()