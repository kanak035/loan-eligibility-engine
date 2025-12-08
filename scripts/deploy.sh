#!/bin/bash

# Deployment script for Loan Eligibility Engine

set -e

echo "🚀 Deploying Loan Eligibility Engine..."

# Check prerequisites
echo "Checking prerequisites..."

if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found. Please install it first."
    exit 1
fi

if ! command -v serverless &> /dev/null; then
    echo "❌ Serverless Framework not found. Please install it: npm install -g serverless"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install it first."
    exit 1
fi

echo "✅ Prerequisites check passed"

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
    echo "✅ Environment variables loaded"
else
    echo "⚠️  .env file not found. Using .env.example as template"
    cp .env.example .env
    echo "❌ Please configure .env file and run again"
    exit 1
fi

# Install dependencies
echo "Installing dependencies..."
npm install
pip install -r requirements.txt
echo "✅ Dependencies installed"

# Store database password in AWS Systems Manager Parameter Store
echo "Storing database password in SSM..."
aws ssm put-parameter \
    --name "/loan-eligibility/${STAGE}/db-password" \
    --value "${DB_PASSWORD}" \
    --type "SecureString" \
    --overwrite \
    --region "${AWS_REGION}" || echo "⚠️  SSM parameter already exists or creation failed"

# Deploy serverless stack
echo "Deploying serverless stack..."
serverless deploy --stage "${STAGE}" --region "${AWS_REGION}"

# Get outputs
echo "Retrieving deployment outputs..."
DB_ENDPOINT=$(aws cloudformation describe-stacks \
    --stack-name "loan-eligibility-engine-${STAGE}" \
    --query 'Stacks[0].Outputs[?OutputKey==`DBEndpoint`].OutputValue' \
    --output text \
    --region "${AWS_REGION}")

CSV_BUCKET=$(aws cloudformation describe-stacks \
    --stack-name "loan-eligibility-engine-${STAGE}" \
    --query 'Stacks[0].Outputs[?OutputKey==`CSVBucketName`].OutputValue' \
    --output text \
    --region "${AWS_REGION}")

API_URL=$(aws cloudformation describe-stacks \
    --stack-name "loan-eligibility-engine-${STAGE}" \
    --query 'Stacks[0].Outputs[?OutputKey==`UploadInitiatorUrl`].OutputValue' \
    --output text \
    --region "${AWS_REGION}")

echo "✅ Serverless stack deployed"
echo "   - DB Endpoint: ${DB_ENDPOINT}"
echo "   - CSV Bucket: ${CSV_BUCKET}"
echo "   - API URL: ${API_URL}"

# Initialize database
echo "Initializing database..."
export DB_HOST="${DB_ENDPOINT}"
python scripts/init_db.py || echo "⚠️  Database initialization failed. You may need to run it manually."

# Update .env with actual values
sed -i.bak "s|DB_HOST=.*|DB_HOST=${DB_ENDPOINT}|" .env
echo "✅ .env file updated with RDS endpoint"

# Start n8n container
echo "Starting n8n container..."
docker-compose up -d

echo "✅ n8n container started"
echo "   Access n8n at: http://localhost:5678"
echo "   Username: ${N8N_BASIC_AUTH_USER}"
echo "   Password: ${N8N_BASIC_AUTH_PASSWORD}"

# Update frontend with API URL
sed -i.bak "s|const API_ENDPOINT = .*|const API_ENDPOINT = '${API_URL}';|" frontend/index.html
echo "✅ Frontend updated with API endpoint"

echo ""
echo "🎉 Deployment completed successfully!"
echo ""
echo "Next steps:"
echo "1. Access n8n at http://localhost:5678"
echo "2. Import workflows from n8n-workflows/ directory"
echo "3. Configure credentials in n8n (PostgreSQL, AWS SES, Gemini API)"
echo "4. Verify SES email address in AWS Console"
echo "5. Open frontend/index.html in a browser to upload CSV files"
echo ""
echo "📖 See README.md for detailed instructions"
