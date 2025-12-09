# Loan Eligibility Engine - SDE Intern Backend Assignment

An automated system that ingests user data, discovers personal loan products from public websites, matches users to eligible products, and notifies them via email.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         AWS Cloud Environment                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌──────────────┐      ┌─────────────────┐                         │
│  │   S3 Bucket  │─────▶│  Lambda (CSV    │                         │
│  │  (CSV Files) │      │   Processor)    │                         │
│  └──────────────┘      └────────┬────────┘                         │
│                                  │                                   │
│                                  ▼                                   │
│  ┌──────────────┐      ┌─────────────────┐      ┌──────────────┐  │
│  │ API Gateway  │─────▶│  Lambda (Upload │─────▶│     RDS      │  │
│  │  (Optional)  │      │   Initiator)    │      │ PostgreSQL   │  │
│  └──────────────┘      └─────────────────┘      │              │  │
│                                                   │  - users     │  │
│                                                   │  - products  │  │
│                        ┌──────────────┐          │  - matches   │  │
│                        │  SES (Email) │◀─────────┴──────────────┘  │
│                        └──────────────┘                             │
│                                 ▲                                    │
└─────────────────────────────────┼────────────────────────────────────┘
                                  │
                                  │ HTTPS/Webhook
                                  │
┌─────────────────────────────────┼────────────────────────────────────┐
│                    Docker Container (Self-Hosted)                    │
├─────────────────────────────────┴────────────────────────────────────┤
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                       n8n Workflows                          │   │
│  ├─────────────────────────────────────────────────────────────┤   │
│  │                                                              │   │
│  │  Workflow A: Loan Product Discovery (Scheduled Daily)       │   │
│  │  ┌──────────┐   ┌──────────┐   ┌──────────┐                │   │
│  │  │ Schedule │──▶│   HTTP   │──▶│PostgreSQL│                │   │
│  │  │ Trigger  │   │  Crawler │   │  Insert  │                │   │
│  │  └──────────┘   └──────────┘   └──────────┘                │   │
│  │                                                              │   │
│  │  Workflow B: User-Loan Matching (Webhook Triggered)         │   │
│  │  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌─────────┐ │   │
│  │  │ Webhook  │──▶│PostgreSQL│──▶│ Filtering│──▶│PostgreSQL│ │   │
│  │  │ Trigger  │   │  Fetch   │   │  Logic   │   │  Insert  │ │   │
│  │  └──────────┘   └──────────┘   └──────────┘   └─────────┘ │   │
│  │                                                              │   │
│  │  Workflow C: User Notification (After Matching)             │   │
│  │  ┌──────────┐   ┌──────────┐   ┌──────────┐                │   │
│  │  │PostgreSQL│──▶│  Email   │──▶│   AWS    │                │   │
│  │  │  Fetch   │   │ Template │   │   SES    │                │   │
│  │  └──────────┘   └──────────┘   └──────────┘                │   │
│  │                                                              │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────┐
│                         Frontend (Simple UI)                          │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │  HTML Form ──▶ Upload CSV to S3 via Pre-signed URL           │    │
│  └──────────────────────────────────────────────────────────────┘    │
└───────────────────────────────────────────────────────────────────────┘
```

## 🚀 Tech Stack

- **Backend**: Python 3.9+
- **Cloud**: AWS (Lambda, S3, RDS PostgreSQL, SES)
- **Workflow Automation**: n8n (Self-hosted via Docker)
- **AI**: Google Gemini API (Free Tier)
- **Deployment**: Serverless Framework
- **Containerization**: Docker Compose

## 📋 Prerequisites

- Python 3.9 or higher
- Node.js 16+ and npm
- Docker and Docker Compose
- AWS Account (Free Tier)
- AWS CLI configured with credentials
- Serverless Framework (`npm install -g serverless`)

## 🛠️ Setup Instructions

### 1. Clone the Repository

```bash
git clone <repository-url>
cd loan-eligibility-engine
```

### 2. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Serverless plugins
npm install
```

### 3. Configure Environment Variables

Create a `.env` file in the root directory:

```env
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=your-account-id

# Database Configuration
DB_HOST=your-rds-endpoint
DB_PORT=5432
DB_NAME=loan_eligibility
DB_USER=postgres
DB_PASSWORD=your-secure-password

# SES Configuration
SES_FROM_EMAIL=your-verified-email@example.com

# n8n Configuration
N8N_ENCRYPTION_KEY=your-encryption-key
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=your-secure-password

# AI API Configuration
GEMINI_API_KEY=your-gemini-api-key
```

### 4. Deploy AWS Infrastructure

```bash
# Deploy serverless stack
serverless deploy --stage dev

# Note the outputs: S3 bucket name, RDS endpoint, API endpoints
```

### 5. Initialize Database Schema

```bash
# Run database migrations
python scripts/init_db.py
```

### 6. Start n8n Instance

```bash
# Start n8n using Docker Compose
docker-compose up -d

# Access n8n at http://localhost:5678
```

### 7. Import n8n Workflows

1. Open n8n at `http://localhost:5678`
2. Login with credentials from `.env`
3. Import workflows from `n8n-workflows/` directory:
   - `workflow-a-loan-discovery.json`
   - `workflow-b-user-matching.json`
   - `workflow-c-notifications.json`
4. Configure credentials in each workflow:
   - PostgreSQL credentials
   - AWS SES credentials
   - Gemini API key

### 8. Configure n8n Webhooks

After importing workflows, update the webhook URLs in:
- Lambda function environment variables
- Frontend configuration

## 🎯 Usage

### Upload User Data CSV

1. Open the web UI at the deployed CloudFront/S3 URL
2. Upload a CSV file with the following columns:
   - `user_id`, `email`, `monthly_income`, `credit_score`, `employment_status`, `age`
3. The system will automatically:
   - Upload file to S3
   - Process and store user data in RDS
   - Trigger matching workflow via webhook
   - Send notification emails to matched users

### Monitor Workflows

Access n8n dashboard at `http://localhost:5678/workflows` to monitor:
- Workflow execution history
- Error logs
- Data transformations

## 🧠 Design Decisions

### 1. Scalable Data Ingestion Pattern

Instead of direct API Gateway upload (limited to 10MB), we implemented an **event-driven S3 upload pattern**:

- Frontend requests pre-signed S3 URL from Lambda
- Large CSV files upload directly to S3
- S3 event triggers Lambda for async processing
- No timeout or size limitations

### 2. Multi-Stage Filtering Pipeline (Optimization Treasure Hunt)

To handle thousands of users against dozens of loan products efficiently:

**Stage 1: SQL Pre-filtering (Database Layer)**
```sql
-- Fast elimination of obvious mismatches
SELECT u.*, p.* FROM users u
CROSS JOIN loan_products p
WHERE u.monthly_income >= p.min_income
  AND u.credit_score >= p.min_credit_score
  AND u.age >= p.min_age
```
- **Impact**: Reduces candidates by ~70-80%
- **Cost**: Nearly free, milliseconds per query

**Stage 2: Business Rules Filter (n8n Logic)**
- Apply complex eligibility rules (employment status, debt ratios)
- Use n8n's function nodes for custom logic
- **Impact**: Further reduces by ~15-20%
- **Cost**: Free, seconds per batch

**Stage 3: AI-Enhanced Qualification (Gemini API - Optional)**
- Only for ambiguous cases (e.g., borderline scores)
- Batch process remaining ~5-10% of candidates
- Use Gemini for nuanced criteria interpretation
- **Impact**: High-quality final matches
- **Cost**: Minimal API calls

**Result**: From 10,000 potential comparisons → ~500 SQL → ~100 logic checks → ~10-20 AI calls

### 3. Web Crawling Strategy

**Resilient Multi-Source Crawler**:
- Target websites: BankRate, NerdWallet, LendingTree
- Use HTTP Request nodes with custom headers
- Parse HTML with regex and JSON extraction
- Implement retry logic and error handling
- Store raw HTML for debugging
- Extract structured data: `{product_name, interest_rate, min_income, min_credit_score}`

**Fallback Mechanism**:
- If crawling fails, use cached data
- Alert admin via email
- Manual review workflow

### 4. Database Schema Design

**Normalized Structure**:
```
users (user_id PK, email, monthly_income, credit_score, ...)
loan_products (product_id PK, product_name, interest_rate, ...)
eligibility_criteria (criteria_id PK, product_id FK, criterion_type, value)
matches (match_id PK, user_id FK, product_id FK, match_score, created_at)
```

## 📊 Database Schema

```sql
-- Users table
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    monthly_income DECIMAL(10, 2),
    credit_score INTEGER,
    employment_status VARCHAR(50),
    age INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Loan products table
CREATE TABLE loan_products (
    product_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_name VARCHAR(255) NOT NULL,
    provider VARCHAR(255),
    interest_rate DECIMAL(5, 2),
    min_income DECIMAL(10, 2),
    min_credit_score INTEGER,
    min_age INTEGER,
    max_loan_amount DECIMAL(12, 2),
    source_url TEXT,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Matches table
CREATE TABLE matches (
    match_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id),
    product_id UUID REFERENCES loan_products(product_id),
    match_score DECIMAL(3, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notified BOOLEAN DEFAULT FALSE
);
```

## 🔧 AWS Resources Created

- **Lambda Functions**:
  - `csv-upload-initiator`: Generates pre-signed S3 URLs
  - `csv-processor`: Processes uploaded CSV files
  - `webhook-trigger`: Triggers n8n workflows
  
- **S3 Bucket**: Storage for uploaded CSV files

- **RDS PostgreSQL**: Database for users, products, and matches

- **SES**: Email service for notifications

- **IAM Roles**: Least-privilege access for Lambda functions

## 📧 Email Notification Format

```
Subject: You're Pre-Qualified for Personal Loans!

Hi [User Name],

Great news! Based on your profile, you may be eligible for the following personal loan products:

1. [Product Name] by [Provider]
   - Interest Rate: X.XX% APR
   - Estimated Loan Amount: Up to $XX,XXX
   - [Learn More Link]

2. [Product Name] by [Provider]
   ...

Next Steps:
- Click the links above to learn more
- Compare rates and terms
- Apply directly with the lender

This is an automated pre-qualification. Final approval depends on the lender's review.

Best regards,
Loan Eligibility Engine
```

## 🧪 Testing

```bash
# Test Lambda functions locally
serverless invoke local -f csvProcessor -p test/sample-event.json

# Test database connection
python scripts/test_db.py

# Validate n8n workflows
# Use n8n's built-in test execution feature
```

## 🚀 Deployment Checklist

- [ ] AWS credentials configured
- [ ] Environment variables set
- [ ] Database schema initialized
- [ ] n8n workflows imported and activated
- [ ] SES email verified (sandbox mode)
- [ ] Frontend deployed to S3
- [ ] Webhook URLs configured
- [ ] Test end-to-end flow

## 📹 Video Demonstration

[Link to demonstration video - 5-10 minutes]

**Contents**:
1. Architecture walkthrough
2. n8n workflows explanation
3. Live CSV upload demonstration
4. Email notification preview

## 🔐 Security Considerations

- All secrets stored in AWS Secrets Manager / Environment Variables
- Database credentials encrypted at rest
- S3 bucket with encryption enabled
- IAM roles with least-privilege access
- n8n protected with basic auth
- API rate limiting enabled

## 📈 Performance Optimizations

- Batch database operations (INSERT multiple rows)
- Connection pooling for PostgreSQL
- Async Lambda processing
- Indexed database columns (email, user_id, product_id)
- Cached loan products in n8n
- Pagination for large result sets

## 🐛 Troubleshooting

### Issue: CSV upload fails
- Check S3 bucket permissions
- Verify pre-signed URL not expired
- Check CSV format matches schema

### Issue: n8n workflows not triggering
- Verify webhook URLs are correct
- Check n8n container is running: `docker-compose ps`
- Review n8n logs: `docker-compose logs n8n`

### Issue: Emails not sending
- Verify SES email address is verified
- Check SES is out of sandbox mode
- Review Lambda CloudWatch logs

## 📝 License

This project is for educational purposes as part of an SDE Intern assignment.

## 👥 Contributors

- Developer: [Your Name]
- Reviewers: saurabh@clickpe.ai, harsh.srivastav@clickpe.ai

## 🙏 Acknowledgments

- n8n community for workflow automation
- AWS Free Tier for cloud resources
- Google Gemini for AI capabilities
