-- ============================================================================
-- Simple Unanswered Questions Database
-- PostgreSQL Schema
-- ============================================================================

-- Create the database (run as postgres user if needed)
-- CREATE DATABASE unanswered_questions;
-- \c unanswered_questions;

-- ============================================================================
-- Main Table: Unanswered Questions
-- ============================================================================

CREATE TABLE unanswered_questions (
    id SERIAL PRIMARY KEY,
    question_text TEXT NOT NULL,
    category VARCHAR(100),
    asked_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,

    CONSTRAINT question_not_empty CHECK (LENGTH(question_text) > 0)
);

-- ============================================================================
-- Indexes for Performance
-- ============================================================================

CREATE INDEX idx_category ON unanswered_questions(category);
CREATE INDEX idx_created_at ON unanswered_questions(created_at DESC);
CREATE INDEX idx_question_text ON unanswered_questions USING GIN(to_tsvector('english', question_text));

-- ============================================================================
-- Sample Data
-- ============================================================================

INSERT INTO unanswered_questions (question_text, category, asked_by, notes) VALUES
('How do I transition from teaching to software engineering?', 'Career Change', 'user_123', 'User has 10 years teaching experience'),
('What certifications are best for cloud computing careers?', 'Technical Skills', 'user_456', 'Interested in AWS and Azure'),
('How to negotiate salary for a remote position?', 'Salary', 'user_789', 'First remote job offer');

-- ============================================================================
-- Common Queries
-- ============================================================================

-- Get all unanswered questions
-- SELECT * FROM unanswered_questions ORDER BY created_at DESC;

-- Search questions by keyword
-- SELECT * FROM unanswered_questions
-- WHERE to_tsvector('english', question_text) @@ plainto_tsquery('english', 'career change');

-- Get questions by category
-- SELECT * FROM unanswered_questions WHERE category = 'Career Change';

-- Count questions by category
-- SELECT category, COUNT(*) as count
-- FROM unanswered_questions
-- GROUP BY category
-- ORDER BY count DESC;