import json
import sqlite3
from pathlib import Path

DB = Path(__file__).resolve().parent / "documind.db"


def init_db():
    with sqlite3.connect(DB) as con:
        con.execute("""CREATE TABLE IF NOT EXISTS analyses(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            resume_name TEXT, jd_name TEXT, resume_score INTEGER,
            match_percentage INTEGER, matching_skills TEXT,
            missing_skills TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
        con.execute("""CREATE TABLE IF NOT EXISTS interviews(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            resume_name TEXT, jd_name TEXT, level TEXT, focus TEXT,
            num_questions INTEGER, answered INTEGER, overall_score REAL,
            details TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
        # remembers WHICH questions were asked (never your answers) so new interviews can avoid repeats
        con.execute("""CREATE TABLE IF NOT EXISTS asked_questions(
            question TEXT PRIMARY KEY, skill TEXT, category TEXT,
            times INTEGER DEFAULT 0, last_asked TEXT DEFAULT CURRENT_TIMESTAMP)""")


def save_analysis(resume_name, jd_name, resume_score, match_percentage, matching, missing):
    with sqlite3.connect(DB) as con:
        con.execute("INSERT INTO analyses(resume_name,jd_name,resume_score,match_percentage,matching_skills,missing_skills) VALUES(?,?,?,?,?,?)",
                    (resume_name, jd_name, resume_score, match_percentage, ", ".join(matching), ", ".join(missing)))


def get_history():
    with sqlite3.connect(DB) as con:
        con.row_factory = sqlite3.Row
        return [dict(x) for x in con.execute("SELECT * FROM analyses ORDER BY id DESC").fetchall()]


def delete_analysis(row_id):
    with sqlite3.connect(DB) as con:
        con.execute("DELETE FROM analyses WHERE id=?", (row_id,))


# ---------------------------------------------------------------- mock interviews
def save_interview(resume_name, jd_name, level, focus, num_questions, answered, overall_score, summary, results):
    """Store a finished mock interview (summary + per-question results) locally in SQLite."""
    details = json.dumps({"summary": summary, "results": results}, default=str)
    with sqlite3.connect(DB) as con:
        cur = con.execute(
            "INSERT INTO interviews(resume_name,jd_name,level,focus,num_questions,answered,overall_score,details) VALUES(?,?,?,?,?,?,?,?)",
            (resume_name, jd_name, level, focus, num_questions, answered, overall_score, details))
        return cur.lastrowid


def get_interviews():
    with sqlite3.connect(DB) as con:
        con.row_factory = sqlite3.Row
        rows = [dict(x) for x in con.execute("SELECT * FROM interviews ORDER BY id DESC").fetchall()]
    for row in rows:
        try:
            row["details"] = json.loads(row["details"])
        except (TypeError, ValueError):
            row["details"] = {"summary": {}, "results": []}
    return rows


def delete_interview(row_id):
    with sqlite3.connect(DB) as con:
        con.execute("DELETE FROM interviews WHERE id=?", (row_id,))


def delete_all_interviews():
    with sqlite3.connect(DB) as con:
        con.execute("DELETE FROM interviews")
        con.execute("DELETE FROM asked_questions")


# ---------------------------------------------------------------- question memory (for variety)
def record_asked_questions(questions):
    """Remember that these questions were asked (question text only, no answers)."""
    with sqlite3.connect(DB) as con:
        for q in questions:
            con.execute(
                """INSERT INTO asked_questions(question, skill, category, times, last_asked)
                   VALUES(?,?,?,1,CURRENT_TIMESTAMP)
                   ON CONFLICT(question) DO UPDATE SET times = times + 1, last_asked = CURRENT_TIMESTAMP""",
                (q["question"], q.get("skill", ""), q.get("category", "")))


def get_asked_history():
    """{'questions': {text: times}, 'skills': {skill: times}} used by the interview generator."""
    history = {"questions": {}, "skills": {}}
    with sqlite3.connect(DB) as con:
        for question, skill, category, times in con.execute("SELECT question, skill, category, times FROM asked_questions"):
            history["questions"][question] = times
            if category in ("Technical", "Gap") and skill:
                history["skills"][skill] = history["skills"].get(skill, 0) + times
    return history


def clear_asked_questions():
    with sqlite3.connect(DB) as con:
        con.execute("DELETE FROM asked_questions")
