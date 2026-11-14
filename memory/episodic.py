
import sqlite3
import json

from datetime import datetime
from pathlib import Path
from contextlib import contextmanager


class EpisodicMemory:

    def __init__(self, db_path="memory/agent_memory.db"):

        self.db_path = Path(db_path)

        self.db_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        # Create the database tables
        self.create_table()

    # ======================================================
    # DATABASE CONNECTION
    # ======================================================

    @contextmanager
    def get_connection(self):

        # Create a separate connection for each operation
        connection = sqlite3.connect(
            self.db_path,
            timeout=30
        )

        try:
            yield connection

            connection.commit()

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()

    # ======================================================
    # CREATE DATABASE TABLES
    # ======================================================

    def create_table(self):

        with self.get_connection() as connection:

            # Store previous task experiences
            connection.execute("""
                CREATE TABLE IF NOT EXISTS task_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    goal TEXT NOT NULL,
                    status TEXT NOT NULL,
                    execution_history TEXT,
                    created_at TEXT NOT NULL
                )
            """)

            # Store user feedback
            connection.execute("""
                CREATE TABLE IF NOT EXISTS user_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    feedback TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)

    # ======================================================
    # SAVE TASK EXPERIENCE
    # ======================================================

    def save_experience(
        self,
        goal,
        status,
        execution_history
    ):

        with self.get_connection() as connection:

            connection.execute(
                """
                INSERT INTO task_history
                (goal, status, execution_history, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    goal,
                    status,
                    json.dumps(execution_history),
                    datetime.now().isoformat()
                )
            )

    # ======================================================
    # RETRIEVE RECENT TASK EXPERIENCES
    # ======================================================

    def get_recent_experiences(self, limit=5):

        with self.get_connection() as connection:

            cursor = connection.execute(
                """
                SELECT id, goal, status,
                       execution_history, created_at
                FROM task_history
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,)
            )

            rows = cursor.fetchall()

        experiences = []

        for row in rows:

            experiences.append({
                "id": row[0],
                "goal": row[1],
                "status": row[2],
                "execution_history": (
                    json.loads(row[3])
                    if row[3]
                    else []
                ),
                "created_at": row[4]
            })

        return experiences

    # ======================================================
    # SAVE USER FEEDBACK
    # ======================================================

    def save_feedback(self, feedback):

        with self.get_connection() as connection:

            connection.execute(
                """
                INSERT INTO user_feedback
                (feedback, created_at)
                VALUES (?, ?)
                """,
                (
                    feedback,
                    datetime.now().isoformat()
                )
            )

    # ======================================================
    # RETRIEVE RECENT USER FEEDBACK
    # ======================================================

    def get_recent_feedback(self, limit=5):

        with self.get_connection() as connection:

            cursor = connection.execute(
                """
                SELECT feedback, created_at
                FROM user_feedback
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,)
            )

            rows = cursor.fetchall()

        feedback_records = []

        for row in rows:

            feedback_records.append({
                "feedback": row[0],
                "created_at": row[1]
            })

        return feedback_records

    # ======================================================
    # CLOSE
    # ======================================================

    def close(self):

        # Connections are closed automatically
        # after every database operation.
        pass
