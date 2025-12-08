# database_manager.py
import sqlite3
import json
from datetime import datetime
from contextlib import contextmanager
from typing import Dict, Optional


class DatabaseManager:
    def __init__(self, db_file: str = "candidates_database.db"):
        self.db_file = db_file
        self.initialize_database()

    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_file)
        try:
            yield conn
        finally:
            conn.close()

    def initialize_database(self):
        """Create tables if they don't exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS candidates (
                    candidate_id TEXT PRIMARY KEY,
                    candidate_name TEXT NOT NULL,
                    age TEXT,
                    gender TEXT,
                    examiner_name TEXT,
                    additional_notes TEXT,
                    date_created TEXT NOT NULL,
                    total_sessions INTEGER DEFAULT 0,
                    last_session_date TEXT
                )
            """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS test_sessions (
                    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    candidate_id TEXT NOT NULL,
                    session_number INTEGER NOT NULL,
                    test_date TEXT NOT NULL,
                    corsi_span INTEGER,
                    total_trials INTEGER,
                    correct_trials INTEGER,
                    accuracy REAL,
                    data_files TEXT,
                    FOREIGN KEY (candidate_id) REFERENCES candidates (candidate_id)
                )
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_sessions_candidate 
                ON test_sessions(candidate_id)
            """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_sessions_date 
                ON test_sessions(test_date)
            """
            )

            conn.commit()
        print("✓ Database initialised")

    def save_candidate(self, candidate_info: Dict) -> bool:
        """Insert or update a candidate."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                cursor.execute(
                    "SELECT candidate_id FROM candidates WHERE candidate_id = ?",
                    (candidate_info["candidate_id"],),
                )
                existing = cursor.fetchone()

                if existing:
                    cursor.execute(
                        """
                        UPDATE candidates
                        SET candidate_name = ?, age = ?, gender = ?,
                            examiner_name = ?, additional_notes = ?,
                            last_session_date = ?
                        WHERE candidate_id = ?
                    """,
                        (
                            candidate_info["candidate_name"],
                            candidate_info.get("age"),
                            candidate_info.get("gender"),
                            candidate_info.get("examiner_name"),
                            candidate_info.get("additional_notes"),
                            now,
                            candidate_info["candidate_id"],
                        ),
                    )
                else:
                    cursor.execute(
                        """
                        INSERT INTO candidates
                        (candidate_id, candidate_name, age, gender, examiner_name,
                         additional_notes, date_created, total_sessions, last_session_date)
                        VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?)
                    """,
                        (
                            candidate_info["candidate_id"],
                            candidate_info["candidate_name"],
                            candidate_info.get("age"),
                            candidate_info.get("gender"),
                            candidate_info.get("examiner_name"),
                            candidate_info.get("additional_notes"),
                            now,
                            now,
                        ),
                    )

                conn.commit()
            return True
        except Exception as e:
            print("✗ Error saving candidate:", e)
            return False

    def save_test_session(self, candidate_id: str, session_data: Dict) -> bool:
        """Save test session results."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    UPDATE candidates
                    SET total_sessions = total_sessions + 1,
                        last_session_date = ?
                    WHERE candidate_id = ?
                """,
                    (session_data["test_date"], candidate_id),
                )

                cursor.execute(
                    """
                    INSERT INTO test_sessions
                    (candidate_id, session_number, test_date, corsi_span,
                     total_trials, correct_trials, accuracy, data_files)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        candidate_id,
                        session_data["session_number"],
                        session_data["test_date"],
                        session_data["corsi_span"],
                        session_data["total_trials"],
                        session_data["correct_trials"],
                        session_data["accuracy"],
                        json.dumps(session_data.get("data_files", [])),
                    ),
                )

                conn.commit()
            return True
        except Exception as e:
            print("✗ Error saving test session:", e)
            return False

    def get_stats(self) -> Optional[Dict]:
        """Return counts and recent sessions."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("SELECT COUNT(*) FROM candidates")
                candidate_count = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM test_sessions")
                session_count = cursor.fetchone()[0]

                cursor.execute(
                    """
                    SELECT c.candidate_name, t.session_number, t.corsi_span, t.test_date
                    FROM test_sessions t
                    JOIN candidates c ON t.candidate_id = c.candidate_id
                    ORDER BY t.test_date DESC
                    LIMIT 5
                """
                )
                recent = cursor.fetchall()

                return {
                    "candidate_count": candidate_count,
                    "session_count": session_count,
                    "recent_sessions": recent,
                }
        except Exception as e:
            print("✗ Database error:", e)
            return None
