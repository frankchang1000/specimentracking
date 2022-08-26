import sqlite3 as sql

# create a database called database.db if it doesn't exist

def create_database():
    conn = sql.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT
        )''')
    conn.commit()
    conn.close()

if __name__ == '__main__':
    create_database()
    

