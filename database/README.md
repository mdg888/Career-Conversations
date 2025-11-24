# Unanswered Questions Database

A simple PostgreSQL database system for storing and managing unanswered questions.

## Quick Setup Guide

Follow these steps in order to set up your database:

### Step 1: Install PostgreSQL

1. Go to [postgresql.org/download/windows](https://www.postgresql.org/download/windows/)
2. Download the installer for Windows
3. Run the installer and follow these settings:
   - Remember the password you set for the `postgres` user
   - Keep the default port: `5432`
   - Install pgAdmin (a visual database manager) - this is helpful

### Step 2: Create the Database

**Option A: Using pgAdmin (Visual Tool - Easier)**
1. Open pgAdmin from your Start Menu
2. Enter your postgres password when prompted
3. Right-click on "Databases" in the left panel
4. Select "Create" > "Database"
5. Enter database name: `unanswered_questions`
6. Click "Save"

**Option B: Using Command Line**
```bash
# Open Command Prompt and run:
psql -U postgres

# Enter your postgres password when prompted
# Then type this command:
CREATE DATABASE unanswered_questions;

# Exit psql:
\q
```

### Step 3: Install Python Database Package

Your `requirements.txt` already includes `psycopg2-binary`, so just run:
```bash
pip install -r requirements.txt
```

### Step 4: Set Up Database Tables

From your project directory, run:
```bash
psql -U postgres -d unanswered_questions -f database\schema.sql
```

This creates the `unanswered_questions` table with sample data.

### Step 5: Test the Connection

Run this test command:
```bash
python database\question_db.py
```

If you see question IDs and statistics printed, your setup is complete!

## Usage

### Using Python

```python
from question_db import QuestionDB

# Initialize
db = QuestionDB()

# Add a question
question_id = db.add_question(
    question_text="How do I transition to a new career?",
    category="Career Change",
    asked_by="user_123",
    notes="User has 10 years experience"
)

# Get all questions
questions = db.get_all_questions()
for q in questions:
    print(f"{q['id']}: {q['question_text']}")

# Search questions
results = db.search_questions("career")

# Get questions by category
career_questions = db.get_by_category("Career Change")

# Delete a question (when answered)
db.delete_question(question_id)

# Get statistics
stats = db.get_category_stats()
```

### Using SQL Directly

```sql
-- Add a question
INSERT INTO unanswered_questions (question_text, category, asked_by, notes)
VALUES ('Your question here', 'Category Name', 'user_id', 'Optional notes');

-- View all questions
SELECT * FROM unanswered_questions ORDER BY created_at DESC;

-- Search questions
SELECT * FROM unanswered_questions
WHERE to_tsvector('english', question_text) @@ plainto_tsquery('english', 'keyword');

-- Delete answered questions
DELETE FROM unanswered_questions WHERE id = 1;
```

## Database Schema

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Unique question ID |
| question_text | TEXT | The question |
| category | VARCHAR(100) | Question category |
| asked_by | VARCHAR(100) | Who asked |
| created_at | TIMESTAMP | When created |
| notes | TEXT | Additional notes |

## Configuration

Set the database connection string using environment variable:

```bash
export DATABASE_URL="postgresql://username:password@localhost/unanswered_questions"
```

Or pass it directly in Python:

```python
db = QuestionDB("postgresql://localhost/unanswered_questions")
```

## Common Categories

- Career Change
- Technical Skills
- Job Search
- Interview Prep
- Salary
- Networking
- Education