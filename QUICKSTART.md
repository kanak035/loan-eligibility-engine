# 🚀 Quick Start Guide

Get the Loan Eligibility Engine up and running in under 30 minutes!

## Prerequisites Check

```bash
# Check installations
python --version    # Need 3.9+
node --version      # Need 16+
aws --version       # AWS CLI configured
docker --version    # Docker running
serverless --version # Serverless Framework
```

## 5-Minute Setup

### 1. Configure Environment (2 minutes)

```bash
# Copy example file
cp .env.example .env

# Edit .env with your values
# Required minimum:
# - DB_PASSWORD (create a strong password)
# - SES_FROM_EMAIL (your verified email)
# - GEMINI_API_KEY (get from https://makersuite.google.com/app/apikey)
# - N8N_ENCRYPTION_KEY (generate random 32+ chars)
```

### 2. Install Dependencies (1 minute)

```bash
# Python
pip install -r requirements.txt

# Node
npm install
```

### 3. Deploy to AWS (2 minutes)

```bash
# Store DB password in AWS
aws ssm put-parameter \
  --name "/loan-eligibility/dev/db-password" \
  --value "YOUR_DB_PASSWORD" \
  --type "SecureString"

# Deploy
serverless deploy --stage dev
```

**Save the outputs**: DB endpoint, S3 bucket, API URL

## 10-Minute Database Setup

### 4. Initialize Database (3 minutes)

```bash
# Update .env with RDS endpoint from deployment outputs
# Example: DB_HOST=your-db.xxxxx.us-east-1.rds.amazonaws.com

# Run initialization
python scripts/init_db.py

# Should see: ✓ Database schema created successfully!
```

### 5. Verify Database (1 minute)

```bash
python scripts/test_db.py

# Should see: ✓ Connected successfully!
```

## 10-Minute n8n Setup

### 6. Start n8n (1 minute)

```bash
docker-compose up -d

# Wait 30 seconds for container to start
# Open: http://localhost:5678
```

### 7. Configure Credentials (3 minutes)

In n8n web interface:

**PostgreSQL:**
- Go to: Credentials → New → Postgres
- Name: `Loan Eligibility DB`
- Host: (from .env DB_HOST)
- Database: `loan_eligibility_db`
- User: `postgres`
- Password: (from .env DB_PASSWORD)
- SSL: Enable

**AWS SES:**
- Credentials → New → AWS
- Name: `AWS Credentials`
- Access Key / Secret: (your AWS credentials)
- Region: `us-east-1`

**Gemini API:**
- Credentials → New → HTTP Header Auth
- Name: `Gemini API Key`
- Header Name: `x-goog-api-key`
- Value: (from .env GEMINI_API_KEY)

### 8. Import Workflows (3 minutes)

For each workflow file in `n8n-workflows/`:

1. Workflows → Import from File
2. Select the JSON file
3. Open the workflow
4. Click on each node with a credential icon
5. Select the matching credential
6. Save workflow
7. Activate (toggle in top-right)

### 9. Update Webhook URL (1 minute)

1. Open Workflow B in n8n
2. Click on Webhook node
3. Copy the webhook URL
4. Update `.env`: `N8N_WEBHOOK_URL=http://localhost:5678/webhook/user-matching`
5. Redeploy Lambda: `serverless deploy function -f csvProcessor`

## 5-Minute Testing

### 10. Test End-to-End (5 minutes)

```bash
# Update frontend with API URL (from deployment outputs)
# Edit frontend/index.html, line ~200:
# const API_ENDPOINT = 'YOUR_API_GATEWAY_URL/upload/initiate';

# Open in browser
open frontend/index.html  # macOS
# or just double-click the file

# Upload test/sample-users.csv
# Click "Upload & Process"
```

**Watch the magic happen:**
1. ✅ File uploads to S3
2. ✅ Lambda processes CSV
3. ✅ Users inserted to database
4. ✅ n8n matching workflow runs
5. ✅ Matches created
6. ✅ Emails sent (check inbox!)

### 11. Verify Results

```bash
# Check n8n executions
# Go to: http://localhost:5678/executions
# Should see successful runs of Workflow B

# Or query database directly
python -c "
import psycopg2
import os
from dotenv import load_dotenv
load_dotenv()

conn = psycopg2.connect(
    host=os.getenv('DB_HOST'),
    port=os.getenv('DB_PORT'),
    database=os.getenv('DB_NAME'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD')
)
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM users')
print(f'Users: {cur.fetchone()[0]}')
cur.execute('SELECT COUNT(*) FROM matches')
print(f'Matches: {cur.fetchone()[0]}')
conn.close()
"
```

## Common Issues & Quick Fixes

### ❌ "Can't connect to database"
```bash
# Check RDS security group allows your IP
# Add your IP to inbound rules for port 5432
# Or enable public access (dev only!)
```

### ❌ "SES emails not sending"
```bash
# Verify your email in SES
aws ses verify-email-identity --email-address your@email.com
# Check email for verification link
```

### ❌ "n8n webhook not triggering"
```bash
# Test webhook manually
curl -X POST http://localhost:5678/webhook/user-matching \
  -H "Content-Type: application/json" \
  -d '{"test": true}'
  
# Should return 200 OK
```

### ❌ "Lambda timeout"
```bash
# Check CloudWatch logs
serverless logs -f csvProcessor -t

# If too slow, reduce batch size in csv_processor.py
# Or increase Lambda timeout in serverless.yml
```

## Next Steps

Once everything works:

1. ✅ **Customize workflows** - Edit n8n workflows for your needs
2. ✅ **Add more loan sources** - Extend Workflow A
3. ✅ **Improve matching logic** - Enhance Workflow B filters
4. ✅ **Design better emails** - Customize Workflow C templates
5. ✅ **Deploy to production** - Use `--stage prod`
6. ✅ **Record demo video** - Follow VIDEO_SCRIPT.md
7. ✅ **Submit project** - Push to GitHub, invite reviewers

## Monitoring

```bash
# Watch Lambda logs
serverless logs -f csvProcessor -t

# Watch n8n logs
docker-compose logs -f n8n

# Check database
python scripts/test_db.py
```

## Cleanup (When Done)

```bash
# Remove AWS resources
serverless remove --stage dev

# Stop n8n
docker-compose down

# Remove volumes (optional)
docker-compose down -v
```

## Support

- 📖 Full docs: README.md
- 🏗️ Architecture: ARCHITECTURE.md  
- 🔧 Detailed setup: SETUP_GUIDE.md
- ✅ Checklist: CHECKLIST.md
- 🎬 Video script: VIDEO_SCRIPT.md

## Time Breakdown

- Setup: 5 minutes ✅
- Database: 10 minutes ✅
- n8n: 10 minutes ✅
- Testing: 5 minutes ✅

**Total: ~30 minutes** to fully deployed and tested system! 🎉

---

**Pro Tip**: Star the repo, fork it, and customize for your own projects!
