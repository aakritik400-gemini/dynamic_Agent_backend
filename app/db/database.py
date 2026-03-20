import sqlite3

DB_PATH = "app/db/agents.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS agents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        prompt TEXT NOT NULL,
        type TEXT NOT NULL,
        data_file TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS agent_handoffs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        parent_agent_id INTEGER,
        child_agent_id INTEGER
    )
    """)

    conn.commit()
    conn.close()