# Architecture Deep Dive - Loan Eligibility Engine

## System Overview

The Loan Eligibility Engine is a serverless, event-driven system that automates the process of matching users with personal loan products. It leverages AWS cloud services, n8n workflow automation, and AI to provide an efficient, scalable solution.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          USER INTERFACE LAYER                            │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  Static Website (S3 + CloudFront)                              │    │
│  │  - Single Page Application                                      │    │
│  │  - CSV Upload Interface                                         │    │
│  │  - Direct S3 Upload via Pre-signed URLs                        │    │
│  └────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          API & INGESTION LAYER                           │
│  ┌──────────────────┐         ┌──────────────────┐                     │
│  │  API Gateway     │────────▶│  Lambda          │                     │
│  │  (Optional)      │         │  uploadInitiator │                     │
│  │                  │         │  - Generate URL  │                     │
│  └──────────────────┘         └──────────────────┘                     │
│                                         │                                │
│                                         ▼                                │
│  ┌──────────────────────────────────────────────────────────────┐      │
│  │  S3 Bucket (Encrypted, Versioned)                            │      │
│  │  - CSV Files Storage                                          │      │
│  │  - Event Notifications                                        │      │
│  └──────────────────────────────────────────────────────────────┘      │
│                                   │                                      │
│                                   ▼                                      │
│  ┌──────────────────────────────────────────────────────────────┐      │
│  │  Lambda: csvProcessor (Event-Driven)                         │      │
│  │  - Parse CSV                                                  │      │
│  │  - Validate Data                                              │      │
│  │  - Batch Insert to RDS                                        │      │
│  │  - Trigger n8n Webhook                                        │      │
│  └──────────────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          DATA PERSISTENCE LAYER                          │
│  ┌──────────────────────────────────────────────────────────────┐      │
│  │  RDS PostgreSQL (Multi-AZ for Production)                    │      │
│  │                                                               │      │
│  │  ┌─────────────┐  ┌──────────────┐  ┌─────────────┐         │      │
│  │  │   users     │  │loan_products │  │   matches   │         │      │
│  │  ├─────────────┤  ├──────────────┤  ├─────────────┤         │      │
│  │  │ user_id PK  │  │ product_id PK│  │ match_id PK │         │      │
│  │  │ email       │  │ product_name │  │ user_id FK  │         │      │
│  │  │ income      │  │ interest_rate│  │ product_id  │         │      │
│  │  │ credit_score│  │ min_income   │  │ match_score │         │      │
│  │  │ employment  │  │ min_credit   │  │ notified    │         │      │
│  │  │ age         │  │ source_url   │  │ created_at  │         │      │
│  │  └─────────────┘  └──────────────┘  └─────────────┘         │      │
│  │                                                               │      │
│  │  Indexes: email, income, credit_score, match_score          │      │
│  └──────────────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      WORKFLOW AUTOMATION LAYER (n8n)                     │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │                    Workflow A: Product Discovery                │    │
│  │  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐    │    │
│  │  │ Schedule │──▶│   HTTP   │──▶│  Parse   │──▶│PostgreSQL│    │    │
│  │  │ (Daily)  │   │  Crawl   │   │  Extract │   │  Insert  │    │    │
│  │  └──────────┘   └──────────┘   └──────────┘   └──────────┘    │    │
│  │                                                                  │    │
│  │  Sources: BankRate, NerdWallet, LendingTree                    │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │                  Workflow B: User-Loan Matching                 │    │
│  │  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐    │    │
│  │  │ Webhook  │──▶│PostgreSQL│──▶│ Stage 1: │──▶│ Stage 2: │    │    │
│  │  │ Trigger  │   │  Fetch   │   │SQL Filter│   │ Business │    │    │
│  │  └──────────┘   └──────────┘   └──────────┘   │  Rules   │    │    │
│  │                                                 └────┬─────┘    │    │
│  │                                                      │          │    │
│  │                                    ┌─────────────────┘          │    │
│  │                                    ▼                            │    │
│  │                          ┌──────────────────┐                   │    │
│  │                          │  Ambiguous?      │                   │    │
│  │                          └────┬────────┬────┘                   │    │
│  │                               │        │                        │    │
│  │                        No     │        │ Yes                    │    │
│  │                               │        ▼                        │    │
│  │                               │  ┌──────────┐                   │    │
│  │                               │  │ Stage 3: │                   │    │
│  │                               │  │ Gemini AI│                   │    │
│  │                               │  └──────────┘                   │    │
│  │                               │        │                        │    │
│  │                               ▼        ▼                        │    │
│  │                          ┌──────────────────┐                   │    │
│  │                          │  Merge Results   │                   │    │
│  │                          └────────┬─────────┘                   │    │
│  │                                   ▼                             │    │
│  │                          ┌──────────────────┐                   │    │
│  │                          │PostgreSQL Insert │                   │    │
│  │                          └──────────────────┘                   │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │                 Workflow C: User Notification                   │    │
│  │  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐    │    │
│  │  │ Schedule │──▶│PostgreSQL│──▶│  Build   │──▶│   AWS    │    │    │
│  │  │(15 min)  │   │  Fetch   │   │  Email   │   │   SES    │    │    │
│  │  └──────────┘   └──────────┘   └──────────┘   └──────────┘    │    │
│  │                                                       │         │    │
│  │                                                       ▼         │    │
│  │                                              ┌──────────────┐   │    │
│  │                                              │Update matches│   │    │
│  │                                              │  (notified)  │   │    │
│  │                                              └──────────────┘   │    │
│  └────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        NOTIFICATION & AI LAYER                           │
│  ┌──────────────────┐         ┌──────────────────┐                     │
│  │  AWS SES         │         │  Google Gemini   │                     │
│  │  - Send Emails   │         │  - AI Matching   │                     │
│  │  - Track Status  │         │  - Qualification │                     │
│  └──────────────────┘         └──────────────────┘                     │
└─────────────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Frontend Layer

**Technology**: Static HTML/CSS/JavaScript

**Responsibilities**:
- Present simple upload interface
- Request pre-signed S3 URL from Lambda
- Upload CSV directly to S3 (bypasses API Gateway limits)
- Display upload progress and status

**Key Features**:
- Drag-and-drop file upload
- Client-side CSV validation
- Progress indication
- Error handling

### 2. API Gateway (Optional)

**Purpose**: RESTful API endpoints

**Endpoints**:
- `POST /upload/initiate` - Generate pre-signed S3 URL

**Configuration**:
- CORS enabled
- Rate limiting: 10 requests/second
- API key authentication (optional)

### 3. Lambda Functions

#### uploadInitiator
- **Trigger**: API Gateway POST request
- **Purpose**: Generate pre-signed S3 URLs
- **Runtime**: Python 3.9
- **Memory**: 512 MB
- **Timeout**: 30 seconds

#### csvProcessor
- **Trigger**: S3 ObjectCreated event
- **Purpose**: Process uploaded CSV files
- **Runtime**: Python 3.9
- **Memory**: 512 MB
- **Timeout**: 300 seconds (5 minutes)
- **Concurrency**: 5 (prevents database overload)

**Processing Steps**:
1. Download CSV from S3
2. Parse with pandas
3. Validate data (credit scores, income, age)
4. Batch insert to PostgreSQL (100 rows/batch)
5. Trigger n8n webhook

### 4. Database Layer (RDS PostgreSQL)

**Configuration**:
- Engine: PostgreSQL 14.7
- Instance: db.t3.micro (Free Tier)
- Storage: 20 GB SSD
- Backups: 7-day retention
- Multi-AZ: Disabled (dev), Enabled (prod)

**Schema Design**:
- **Normalized structure** for data integrity
- **Indexes** on frequently queried columns
- **Foreign keys** for referential integrity
- **Views** for complex queries
- **Triggers** for automatic timestamp updates

**Performance**:
- Connection pooling in Lambda
- Batch inserts (100 rows)
- Indexed queries
- Materialized views for reporting

### 5. n8n Workflow Engine

**Deployment**: Docker container (self-hosted)

**Configuration**:
- PostgreSQL backend (persistent executions)
- Basic auth protection
- Webhook endpoints enabled
- Scheduled triggers active

#### Workflow A: Product Discovery

**Trigger**: Cron schedule (daily at 2 AM)

**Nodes**:
1. **Schedule Trigger**: Daily execution
2. **HTTP Request**: Crawl financial websites
3. **Function**: Parse HTML, extract loan data
4. **PostgreSQL**: Insert/update products

**Error Handling**:
- Retry logic on HTTP failures
- Store raw HTML for debugging
- Alert on parsing failures

#### Workflow B: User-Loan Matching

**Trigger**: Webhook (from Lambda)

**Multi-Stage Filtering**:

**Stage 1: SQL Pre-Filter (70-80% reduction)**
```javascript
// Fast numeric comparisons
income >= min_income
credit_score >= min_credit_score
age >= min_age AND age <= max_age
```

**Stage 2: Business Rules (15-20% reduction)**
```javascript
// Complex eligibility logic
- Employment status validation
- Debt-to-income ratio
- Credit tier matching
- Match score calculation
```

**Stage 3: AI Verification (Only for ambiguous cases)**
```javascript
// Use Gemini API for:
- Match scores 0.3-0.7 (borderline cases)
- Nuanced criteria interpretation
- Final qualification check
```

**Optimization Impact**:
- Without optimization: 10,000 user-product comparisons → 10,000 AI calls
- With optimization: 10,000 → 2,000 (SQL) → 300 (rules) → 50 (AI)
- **Cost reduction**: 99.5%
- **Time reduction**: 95%

#### Workflow C: User Notification

**Trigger**: Schedule (every 15 minutes)

**Process**:
1. Fetch users with new matches (notified=false)
2. Fetch their loan matches
3. Build personalized HTML email
4. Send via AWS SES
5. Update match status (notified=true)

**Email Features**:
- Responsive HTML template
- Product comparison table
- Match scores displayed
- Direct application links
- Unsubscribe option (future)

### 6. External Services

#### AWS SES
- **Purpose**: Email delivery
- **Configuration**: Sandbox mode (dev), Production (prod)
- **Verified emails**: Required for sender and recipients (sandbox)
- **Rate limits**: 1 email/second (sandbox), higher (production)

#### Google Gemini
- **Purpose**: AI-powered matching for ambiguous cases
- **Model**: gemini-pro
- **Rate limits**: 60 requests/minute (free tier)
- **Cost**: Free up to quota

## Data Flow

### Scenario: CSV Upload to Notification

1. **User uploads CSV** via web interface
2. **Frontend requests** pre-signed URL from Lambda
3. **Lambda generates** S3 pre-signed URL (valid 1 hour)
4. **Frontend uploads** file directly to S3
5. **S3 triggers** csvProcessor Lambda
6. **Lambda processes** CSV:
   - Parses 1000 rows
   - Validates data
   - Batch inserts to PostgreSQL (10 batches × 100 rows)
7. **Lambda triggers** n8n webhook
8. **n8n Workflow B** executes:
   - Fetches 1000 users
   - Fetches 50 loan products
   - Stage 1: SQL filters 50,000 → 10,000 pairs
   - Stage 2: Business rules 10,000 → 1,500 pairs
   - Stage 3: AI verifies 200 ambiguous cases
   - Inserts 1,200 final matches
9. **n8n Workflow C** executes (next schedule):
   - Fetches 1000 users with new matches
   - Builds 1000 personalized emails
   - Sends via SES (respects rate limits)
   - Updates match status

**Total Time**: ~5-10 minutes for 1000 users

## Scalability

### Current Limits
- Lambda: 5 concurrent executions
- RDS: db.t3.micro (1 vCPU, 1 GB RAM)
- SES: 1 email/second (sandbox)

### Scale to 10,000 Users
- Increase Lambda concurrency: 20
- Upgrade RDS: db.t3.small (2 vCPU, 2 GB RAM)
- SES production: 14 emails/second
- Add read replicas for reporting queries

### Scale to 100,000 Users
- Lambda: 100 concurrent
- RDS: db.r5.large (2 vCPU, 16 GB RAM) + Multi-AZ
- Use Aurora PostgreSQL for auto-scaling
- Implement SQS queue for email processing
- Add CloudFront CDN for frontend
- Use ElastiCache for session data

## Security

### Data Protection
- **At Rest**: S3 SSE-S3, RDS encryption
- **In Transit**: HTTPS, SSL for database
- **Secrets**: AWS Secrets Manager for credentials

### Access Control
- **IAM Roles**: Least-privilege for Lambda
- **VPC**: RDS in private subnet
- **Security Groups**: Port 5432 only from Lambda
- **n8n**: Basic auth, HTTPS (production)

### Compliance
- **GDPR**: Data deletion on request
- **PCI**: No credit card data stored
- **Audit Logs**: CloudWatch Logs retention (90 days)

## Monitoring & Observability

### Metrics
- **Lambda**: Invocations, errors, duration
- **RDS**: CPU, connections, storage
- **n8n**: Workflow executions, success rate
- **SES**: Sends, bounces, complaints

### Alarms
- Lambda errors > 5%
- RDS CPU > 80%
- RDS storage < 2 GB
- SES bounce rate > 5%

### Dashboards
- CloudWatch dashboard with all metrics
- n8n execution history
- Database query performance (pg_stat_statements)

## Cost Estimation (Monthly)

### AWS Services
- Lambda: $0 (Free Tier: 1M requests)
- RDS db.t3.micro: $0 (Free Tier: 750 hours)
- S3: $1 (100 GB storage, 10,000 uploads)
- SES: $0 (Free Tier: 3,000 emails)
- Data Transfer: $5

### External Services
- Gemini API: $0 (Free Tier)
- n8n: $0 (Self-hosted)

**Total**: ~$6/month (within Free Tier limits)

### Production Scale (10,000 users/month)
- Lambda: $5
- RDS db.t3.small: $25
- S3: $5
- SES: $1 (10,000 emails)
- Data Transfer: $10

**Total**: ~$46/month

## Future Enhancements

1. **Machine Learning**: Train ML model for better matching
2. **Real-time Updates**: WebSocket notifications
3. **User Portal**: Self-service dashboard
4. **A/B Testing**: Test email templates
5. **Analytics**: User behavior tracking
6. **Multi-region**: Deploy in multiple AWS regions
7. **GraphQL API**: For mobile apps
8. **Kubernetes**: Replace Docker Compose with EKS

---

This architecture prioritizes:
- ✅ **Scalability**: Event-driven, serverless
- ✅ **Cost-efficiency**: Free Tier usage, optimized AI calls
- ✅ **Reliability**: Retry logic, error handling
- ✅ **Maintainability**: Modular design, clear separation
- ✅ **Performance**: Multi-stage filtering, batch operations
