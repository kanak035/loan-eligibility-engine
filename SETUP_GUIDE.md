# Detailed Setup Guide - Loan Eligibility Engine

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [AWS Account Setup](#aws-account-setup)
3. [Local Development Setup](#local-development-setup)
4. [Database Setup](#database-setup)
5. [n8n Configuration](#n8n-configuration)
6. [Testing](#testing)
7. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Software
- **Python**: 3.9 or higher
  ```bash
  python --version
  ```

- **Node.js**: 16+ and npm
  ```bash
  node --version
  npm --version
  ```

- **AWS CLI**: Configured with credentials
  ```bash
  aws --version
  aws configure
  ```

- **Docker & Docker Compose**: For running n8n
  ```bash
  docker --version
  docker-compose --version
  ```

- **Serverless Framework**
  ```bash
  npm install -g serverless
  serverless --version
  ```

### Required Accounts
- AWS Account (Free Tier eligible)
- Google Cloud Account (for Gemini API - free tier)
- Email provider for SES verification

## AWS Account Setup

### Step 1: Create AWS Account
1. Go to [AWS Console](https://aws.amazon.com)
2. Create a new account (if you don't have one)
3. Verify your email and set up billing

### Step 2: Create IAM User
```bash
# Create IAM user with programmatic access
aws iam create-user --user-name loan-eligibility-deployer

# Attach necessary policies
aws iam attach-user-policy --user-name loan-eligibility-deployer \
  --policy-arn arn:aws:iam::aws:policy/AdministratorAccess

# Create access keys
aws iam create-access-key --user-name loan-eligibility-deployer
```

Save the Access Key ID and Secret Access Key.

### Step 3: Configure AWS CLI
```bash
aws configure
# Enter:
# - AWS Access Key ID
# - AWS Secret Access Key
# - Default region: us-east-1
# - Default output format: json
```

### Step 4: Verify SES Email
```bash
# Verify sender email for SES
aws ses verify-email-identity --email-address noreply@yourdomain.com

# Check verification status
aws ses get-identity-verification-attributes \
  --identities noreply@yourdomain.com
```

Check your email and click the verification link.

**Important**: In SES Sandbox mode, you can only send to verified email addresses. Request production access to send to any email.

## Local Development Setup

### Step 1: Clone Repository
```bash
git clone <repository-url>
cd loan-eligibility-engine
```

### Step 2: Install Dependencies
```bash
# Python dependencies
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Node dependencies
npm install
```

### Step 3: Configure Environment
```bash
# Copy example env file
cp .env.example .env

# Edit .env file with your configuration
nano .env  # or use your preferred editor
```

Required variables:
```env
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=your-account-id
DB_PASSWORD=YourSecurePassword123!
SES_FROM_EMAIL=noreply@yourdomain.com
N8N_BASIC_AUTH_PASSWORD=SecureN8nPassword123!
N8N_ENCRYPTION_KEY=your-min-32-character-encryption-key
GEMINI_API_KEY=your-gemini-api-key
```

### Step 4: Get Gemini API Key
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Copy and paste into `.env` file

## Database Setup

### Option A: Automatic Deployment
```bash
# Deploy infrastructure (includes RDS)
serverless deploy --stage dev

# Get RDS endpoint
aws cloudformation describe-stacks \
  --stack-name loan-eligibility-engine-dev \
  --query 'Stacks[0].Outputs[?OutputKey==`DBEndpoint`].OutputValue' \
  --output text
```

### Option B: Manual RDS Setup
1. Go to AWS RDS Console
2. Create PostgreSQL database:
   - Engine: PostgreSQL 14.7
   - Template: Free tier
   - DB instance identifier: loan-eligibility-db-dev
   - Master username: postgres
   - Master password: (use value from .env)
   - DB instance class: db.t3.micro
   - Storage: 20 GB
   - Public access: No (if in VPC with Lambda)

### Step 5: Initialize Database Schema
```bash
# Update .env with RDS endpoint
export DB_HOST=your-rds-endpoint.rds.amazonaws.com

# Run initialization script
python scripts/init_db.py

# Test connection
python scripts/test_db.py
```

## n8n Configuration

### Step 1: Start n8n
```bash
# Start n8n container
docker-compose up -d

# Check logs
docker-compose logs -f n8n

# Access n8n
# Open browser: http://localhost:5678
```

### Step 2: Configure Credentials

#### PostgreSQL Credential
1. In n8n, go to **Credentials** → **New**
2. Select **Postgres**
3. Configure:
   - **Name**: Loan Eligibility DB
   - **Host**: Your RDS endpoint
   - **Database**: loan_eligibility_db
   - **User**: postgres
   - **Password**: From .env file
   - **Port**: 5432
   - **SSL**: Enable (for RDS)

#### AWS SES Credential
1. **Credentials** → **New** → **AWS**
2. Configure:
   - **Name**: AWS Credentials
   - **Access Key ID**: Your AWS access key
   - **Secret Access Key**: Your AWS secret key
   - **Region**: us-east-1

#### Gemini API Credential
1. **Credentials** → **New** → **HTTP Header Auth**
2. Configure:
   - **Name**: Gemini API Key
   - **Name**: x-goog-api-key
   - **Value**: Your Gemini API key

### Step 3: Import Workflows

1. **Workflows** → **Import from File**
2. Import each workflow:
   - `n8n-workflows/workflow-a-loan-discovery.json`
   - `n8n-workflows/workflow-b-user-matching.json`
   - `n8n-workflows/workflow-c-notifications.json`

3. For each workflow:
   - Open the workflow
   - Click on each node with credentials
   - Select the credential you created
   - **Save** the workflow
   - **Activate** the workflow

### Step 4: Get Webhook URL

1. Open **Workflow B: User-Loan Matching**
2. Click on the **Webhook** node
3. Copy the webhook URL (e.g., `http://localhost:5678/webhook/user-matching`)
4. Update `.env`:
   ```env
   N8N_WEBHOOK_URL=http://localhost:5678/webhook/user-matching
   ```
5. Redeploy Lambda functions:
   ```bash
   serverless deploy function -f csvProcessor
   ```

## Testing

### Test 1: Database Connection
```bash
python scripts/test_db.py
```

Expected output:
```
✓ Connected successfully!
PostgreSQL version: PostgreSQL 14.7...
```

### Test 2: Sample Data Generation
```bash
python scripts/generate_sample_data.py
```

This creates `test/sample-users-large.csv` with 100 users.

### Test 3: CSV Upload

1. Open `frontend/index.html` in a browser
2. Upload `test/sample-users.csv`
3. Click "Upload & Process"

Expected:
- File uploads to S3
- Lambda processes CSV
- Users inserted into database
- n8n webhook triggered
- Matching workflow executes
- Notification workflow sends emails

### Test 4: Manual Workflow Execution

1. Open n8n: http://localhost:5678
2. Go to **Workflow A: Loan Product Discovery**
3. Click **Execute Workflow** (manually trigger)
4. Verify products are discovered and saved

### Test 5: Check Database

```bash
# Connect to database
psql -h your-rds-endpoint.rds.amazonaws.com \
     -U postgres \
     -d loan_eligibility_db

# Run queries
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM loan_products;
SELECT COUNT(*) FROM matches;

# View matches
SELECT * FROM v_user_matches LIMIT 5;
```

## Troubleshooting

### Issue: Lambda can't connect to RDS

**Solution**: Ensure Lambda and RDS are in the same VPC and security groups allow traffic on port 5432.

```bash
# Check security group rules
aws ec2 describe-security-groups \
  --group-ids sg-xxxxx \
  --query 'SecurityGroups[0].IpPermissions'
```

### Issue: n8n can't connect to RDS

**Solution**: If n8n is running locally and RDS is in VPC with no public access:

1. Enable public access for RDS (development only)
2. Update security group to allow your IP
3. Or use SSH tunnel:
   ```bash
   ssh -L 5432:rds-endpoint:5432 ec2-user@bastion-host
   ```

### Issue: SES emails not sending

**Solutions**:
1. Verify email address in SES console
2. Check if SES is in sandbox mode
3. Request production access if needed
4. Verify recipient email addresses (in sandbox mode)

### Issue: n8n workflows not triggering

**Solutions**:
1. Check workflow is **Activated** (toggle in top-right)
2. Verify webhook URL in Lambda environment variables
3. Check n8n logs: `docker-compose logs n8n`
4. Test webhook manually:
   ```bash
   curl -X POST http://localhost:5678/webhook/user-matching \
     -H "Content-Type: application/json" \
     -d '{"test": true}'
   ```

### Issue: Database migration fails

**Solution**: Manually run SQL:
```bash
psql -h your-rds-endpoint -U postgres -d loan_eligibility_db \
     -f database/schema.sql
```

### Issue: Lambda timeout

**Solution**: Increase timeout in `serverless.yml`:
```yaml
provider:
  timeout: 300  # 5 minutes
```

Then redeploy:
```bash
serverless deploy
```

## Performance Optimization

### Database Indexing
Already included in schema.sql, but verify:
```sql
-- Check indexes
SELECT indexname, tablename FROM pg_indexes 
WHERE schemaname = 'public';
```

### Lambda Concurrency
```bash
# Set reserved concurrency
aws lambda put-function-concurrency \
  --function-name loan-eligibility-engine-dev-csvProcessor \
  --reserved-concurrent-executions 5
```

### RDS Connection Pooling
Update Lambda handler to use connection pooling (already implemented in csv_processor.py).

## Monitoring

### CloudWatch Logs
```bash
# View Lambda logs
serverless logs -f csvProcessor -t

# View specific error logs
aws logs filter-log-events \
  --log-group-name /aws/lambda/loan-eligibility-engine-dev-csvProcessor \
  --filter-pattern "ERROR"
```

### n8n Execution History
1. Open n8n
2. Go to **Executions**
3. View all workflow runs, inputs, outputs

### Database Monitoring
```sql
-- Check recent activity
SELECT * FROM users ORDER BY created_at DESC LIMIT 10;
SELECT * FROM matches ORDER BY created_at DESC LIMIT 10;

-- Match statistics
SELECT 
  DATE(created_at) as date,
  COUNT(*) as matches,
  COUNT(DISTINCT user_id) as users
FROM matches
GROUP BY DATE(created_at)
ORDER BY date DESC;
```

## Next Steps

1. **Customize Workflows**: Modify n8n workflows for your specific requirements
2. **Add More Sources**: Extend Workflow A to crawl additional loan provider websites
3. **Improve Matching**: Enhance the filtering logic in Workflow B
4. **Email Templates**: Customize email design in Workflow C
5. **Production Deployment**: Move from dev to prod stage
6. **CI/CD**: Set up GitHub Actions for automated deployment
7. **Monitoring**: Add CloudWatch alarms and SNS notifications

## Security Checklist

- [ ] Database password stored in AWS Secrets Manager/SSM
- [ ] RDS not publicly accessible (use VPC)
- [ ] n8n protected with strong password
- [ ] API Gateway with rate limiting (if using)
- [ ] S3 bucket encryption enabled
- [ ] IAM roles with least-privilege access
- [ ] SES production access requested (not sandbox)
- [ ] Regular backups enabled for RDS
- [ ] CloudWatch alarms configured
- [ ] Audit logging enabled

---

**Need help?** Check the main README.md or open an issue in the repository.
