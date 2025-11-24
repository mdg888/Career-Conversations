"""
Simple Unanswered Questions Database Interface
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class QuestionDB:
    """Simple interface for managing unanswered questions."""

    def __init__(self, connection_string: Optional[str] = None):
        """
        Initialize database connection.

        Args:
            connection_string: PostgreSQL connection string
                             Default: postgresql://localhost/unanswered_questions
        """
        self.connection_string = connection_string or os.getenv(
            'DATABASE_URL',
            'postgresql://localhost/unanswered_questions'
        )

    def _get_connection(self):
        """Get a database connection."""
        return psycopg2.connect(self.connection_string)

    def add_question(
        self,
        question_text: str,
        category: Optional[str] = None,
        asked_by: Optional[str] = None,
        notes: Optional[str] = None
    ) -> int:
        """
        Add a new unanswered question.

        Args:
            question_text: The question
            category: Question category
            asked_by: Who asked the question
            notes: Additional notes

        Returns:
            ID of the created question
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO unanswered_questions (question_text, category, asked_by, notes)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                """, (question_text, category, asked_by, notes))
                question_id = cur.fetchone()[0]
                conn.commit()
                return question_id
        finally:
            conn.close()

    def get_all_questions(self) -> List[Dict]:
        """
        Get all unanswered questions.

        Returns:
            List of question dictionaries
        """
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM unanswered_questions
                    ORDER BY created_at DESC
                """)
                return [dict(row) for row in cur.fetchall()]
        finally:
            conn.close()

    def search_questions(self, keyword: str) -> List[Dict]:
        """
        Search questions by keyword.

        Args:
            keyword: Search term

        Returns:
            List of matching question dictionaries
        """
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM unanswered_questions
                    WHERE to_tsvector('english', question_text) @@ plainto_tsquery('english', %s)
                    ORDER BY created_at DESC
                """, (keyword,))
                return [dict(row) for row in cur.fetchall()]
        finally:
            conn.close()

    def get_by_category(self, category: str) -> List[Dict]:
        """
        Get questions by category.

        Args:
            category: Category name

        Returns:
            List of question dictionaries
        """
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM unanswered_questions
                    WHERE category = %s
                    ORDER BY created_at DESC
                """, (category,))
                return [dict(row) for row in cur.fetchall()]
        finally:
            conn.close()

    def delete_question(self, question_id: int) -> bool:
        """
        Delete a question (e.g., when it's been answered).

        Args:
            question_id: Question ID

        Returns:
            True if deleted, False if not found
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    DELETE FROM unanswered_questions
                    WHERE id = %s
                    RETURNING id
                """, (question_id,))
                result = cur.fetchone()
                conn.commit()
                return result is not None
        finally:
            conn.close()

    def update_notes(self, question_id: int, notes: str) -> bool:
        """
        Update notes for a question.

        Args:
            question_id: Question ID
            notes: New notes

        Returns:
            True if updated, False if not found
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE unanswered_questions
                    SET notes = %s
                    WHERE id = %s
                    RETURNING id
                """, (notes, question_id))
                result = cur.fetchone()
                conn.commit()
                return result is not None
        finally:
            conn.close()

    def get_category_stats(self) -> List[Dict]:
        """
        Get question count by category.

        Returns:
            List of category statistics
        """
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT category, COUNT(*) as count
                    FROM unanswered_questions
                    GROUP BY category
                    ORDER BY count DESC
                """)
                return [dict(row) for row in cur.fetchall()]
        finally:
            conn.close()


# Example usage
if __name__ == "__main__":
    db = QuestionDB()

    # Add a question
    question_id = db.add_question(
        question_text="How do I switch from marketing to data analysis?",
        category="Career Change",
        asked_by="user_101",
        notes="User has 5 years marketing experience"
    )
    print(f"Added question ID: {question_id}")

    # Get all questions
    questions = db.get_all_questions()
    print(f"\nTotal questions: {len(questions)}")

    # Search questions
    results = db.search_questions("career")
    print(f"\nFound {len(results)} questions about 'career'")

    # Get category stats
    stats = db.get_category_stats()
    print("\nQuestions by category:")
    for stat in stats:
        print(f"  {stat['category']}: {stat['count']}")