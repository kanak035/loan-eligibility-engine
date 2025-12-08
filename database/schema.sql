-- Database initialization script for Loan Eligibility Engine
-- Creates all necessary tables with proper constraints and indexes

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Drop tables if they exist (for clean setup)
DROP TABLE IF EXISTS matches CASCADE;
DROP TABLE IF EXISTS loan_products CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- Users table
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    monthly_income DECIMAL(10, 2) NOT NULL CHECK (monthly_income >= 0),
    credit_score INTEGER NOT NULL CHECK (credit_score BETWEEN 300 AND 850),
    employment_status VARCHAR(50) NOT NULL,
    age INTEGER NOT NULL CHECK (age BETWEEN 18 AND 100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for users table
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_income ON users(monthly_income);
CREATE INDEX idx_users_credit_score ON users(credit_score);
CREATE INDEX idx_users_created_at ON users(created_at);

-- Loan products table
CREATE TABLE loan_products (
    product_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_name VARCHAR(255) NOT NULL,
    provider VARCHAR(255) NOT NULL,
    interest_rate DECIMAL(5, 2) CHECK (interest_rate >= 0),
    min_income DECIMAL(10, 2) DEFAULT 0,
    min_credit_score INTEGER DEFAULT 300 CHECK (min_credit_score BETWEEN 300 AND 850),
    min_age INTEGER DEFAULT 18 CHECK (min_age >= 18),
    max_age INTEGER DEFAULT 100 CHECK (max_age <= 100),
    max_loan_amount DECIMAL(12, 2),
    loan_term_months INTEGER,
    source_url TEXT,
    eligibility_criteria JSONB,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Create indexes for loan_products table
CREATE INDEX idx_products_provider ON loan_products(provider);
CREATE INDEX idx_products_interest_rate ON loan_products(interest_rate);
CREATE INDEX idx_products_active ON loan_products(is_active);
CREATE INDEX idx_products_criteria ON loan_products USING GIN(eligibility_criteria);

-- Matches table (links users to eligible loan products)
CREATE TABLE matches (
    match_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES loan_products(product_id) ON DELETE CASCADE,
    match_score DECIMAL(3, 2) CHECK (match_score BETWEEN 0 AND 1),
    match_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notified BOOLEAN DEFAULT FALSE,
    notified_at TIMESTAMP,
    UNIQUE(user_id, product_id)
);

-- Create indexes for matches table
CREATE INDEX idx_matches_user_id ON matches(user_id);
CREATE INDEX idx_matches_product_id ON matches(product_id);
CREATE INDEX idx_matches_notified ON matches(notified);
CREATE INDEX idx_matches_created_at ON matches(created_at);
CREATE INDEX idx_matches_score ON matches(match_score DESC);

-- Create a composite index for common queries
CREATE INDEX idx_matches_user_product ON matches(user_id, product_id);

-- Create a view for easy querying of matches with user and product details
CREATE OR REPLACE VIEW v_user_matches AS
SELECT 
    m.match_id,
    m.match_score,
    m.match_reason,
    m.created_at as matched_at,
    m.notified,
    m.notified_at,
    u.user_id,
    u.email,
    u.monthly_income,
    u.credit_score,
    u.employment_status,
    u.age,
    p.product_id,
    p.product_name,
    p.provider,
    p.interest_rate,
    p.max_loan_amount,
    p.loan_term_months,
    p.source_url
FROM matches m
JOIN users u ON m.user_id = u.user_id
JOIN loan_products p ON m.product_id = p.product_id;

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update updated_at
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Insert sample loan products for testing
INSERT INTO loan_products (
    product_name, 
    provider, 
    interest_rate, 
    min_income, 
    min_credit_score, 
    min_age,
    max_loan_amount,
    loan_term_months,
    source_url,
    eligibility_criteria
) VALUES 
(
    'Personal Loan - Excellent Credit',
    'Sample Bank',
    5.99,
    50000,
    750,
    21,
    100000,
    60,
    'https://example.com/loan1',
    '{"employment": ["full-time", "self-employed"], "min_tenure_months": 12}'::jsonb
),
(
    'Quick Cash Loan',
    'Fast Finance',
    12.99,
    30000,
    650,
    18,
    50000,
    36,
    'https://example.com/loan2',
    '{"employment": ["full-time", "part-time"], "min_tenure_months": 6}'::jsonb
),
(
    'Premium Personal Loan',
    'Elite Lending',
    4.49,
    75000,
    800,
    25,
    200000,
    84,
    'https://example.com/loan3',
    '{"employment": ["full-time"], "min_tenure_months": 24}'::jsonb
);

-- Grant permissions (adjust as needed for your setup)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_db_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO your_db_user;

-- Display table information
SELECT 
    schemaname,
    tablename,
    tableowner
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;

-- Display row counts
SELECT 'users' as table_name, COUNT(*) as row_count FROM users
UNION ALL
SELECT 'loan_products', COUNT(*) FROM loan_products
UNION ALL
SELECT 'matches', COUNT(*) FROM matches;
