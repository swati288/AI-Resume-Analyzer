import sqlite3

def create_database():

    conn = sqlite3.connect("resumes.db")

    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS resume_analysis (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        name TEXT,

        email TEXT,

        phone TEXT,

        resume_score REAL,

        match_score REAL,

        upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    )
    """)

    conn.commit()
    conn.close()


create_database()

def save_resume_analysis(
    name,
    email,
    phone,
    resume_score,
    match_score
):

    conn = sqlite3.connect("resumes.db")

    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO resume_analysis
    (
        name,
        email,
        phone,
        resume_score,
        match_score
    )

    VALUES (?, ?, ?, ?, ?)
    """,

    (
        name,
        email,
        phone,
        resume_score,
        match_score
    ))

    conn.commit()
    conn.close()