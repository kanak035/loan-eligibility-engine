# Loan Eligibility Engine - Project Checklist

## Pre-Deployment Checklist

### AWS Setup
- [ ] AWS account created
- [ ] IAM user with programmatic access created
- [ ] AWS CLI installed and configured
- [ ] SES email address verified
- [ ] (Optional) SES moved out of sandbox mode

### Local Setup
- [ ] Python 3.9+ installed
- [ ] Node.js 16+ installed
- [ ] Docker and Docker Compose installed
- [ ] Serverless Framework installed globally
- [ ] Repository cloned

### Configuration
- [ ] `.env` file created from `.env.example`
- [ ] All environment variables configured
- [ ] Database password set (secure, 16+ characters)
- [ ] N8N encryption key generated (32+ characters)
- [ ] Gemini API key obtained and set
- [ ] SES from-email set to verified address

### Dependencies
- [ ] Python dependencies installed (`pip install -r requirements.txt`)
- [ ] Node dependencies installed (`npm install`)

## Deployment Checklist

### Infrastructure Deployment
- [ ] Database password stored in AWS SSM Parameter Store
- [ ] Serverless stack deployed (`serverless deploy`)
- [ ] RDS endpoint retrieved from outputs
- [ ] S3 bucket name retrieved from outputs
- [ ] API Gateway URL retrieved from outputs
- [ ] `.env` file updated with actual values

### Database Setup
- [ ] Database schema initialized (`python scripts/init_db.py`)
- [ ] Sample loan products inserted
- [ ] Database connection tested (`python scripts/test_db.py`)
- [ ] Tables verified (users, loan_products, matches)

### n8n Setup
- [ ] Docker container started (`docker-compose up -d`)
- [ ] n8n accessible at http://localhost:5678
- [ ] PostgreSQL credential created in n8n
- [ ] AWS SES credential created in n8n
- [ ] Gemini API credential created in n8n
- [ ] Workflow A imported and configured
- [ ] Workflow B imported and configured
- [ ] Workflow C imported and configured
- [ ] All workflows activated
- [ ] Webhook URL copied to `.env`
- [ ] Lambda environment variables updated

### Frontend Setup
- [ ] `frontend/index.html` updated with API endpoint
- [ ] Frontend tested with sample CSV
- [ ] CORS configured correctly

## Testing Checklist

### Unit Tests
- [ ] Database connection works
- [ ] Lambda functions can access RDS
- [ ] S3 upload generates pre-signed URLs
- [ ] CSV parsing works correctly
- [ ] Data validation catches invalid inputs

### Integration Tests
- [ ] Complete CSV upload flow works
- [ ] Users inserted into database
- [ ] n8n webhook triggered correctly
- [ ] Matching workflow executes successfully
- [ ] Matches saved to database
- [ ] Notification workflow sends emails
- [ ] Email received and formatted correctly

### Load Tests (Optional)
- [ ] Upload 100 users - processed successfully
- [ ] Upload 1000 users - no timeouts
- [ ] Concurrent uploads handled correctly

## Documentation Checklist

### Code Documentation
- [ ] All functions have docstrings
- [ ] Complex logic explained with comments
- [ ] SQL queries commented
- [ ] n8n workflow nodes have descriptions

### Project Documentation
- [ ] README.md complete and accurate
- [ ] SETUP_GUIDE.md covers all setup steps
- [ ] ARCHITECTURE.md explains design decisions
- [ ] VIDEO_SCRIPT.md ready for recording
- [ ] All file paths and commands verified

### Repository
- [ ] `.gitignore` includes sensitive files
- [ ] Sample data files included
- [ ] Test files provided
- [ ] Scripts executable (`chmod +x scripts/*.sh`)

## Video Demonstration Checklist

### Pre-Recording
- [ ] All systems running (AWS, n8n, database)
- [ ] Sample data prepared
- [ ] Screen recording software ready
- [ ] Microphone tested
- [ ] Demo script reviewed

### Recording Content
- [ ] Introduction (30 sec)
- [ ] Architecture overview (1 min)
- [ ] AWS infrastructure walkthrough (1 min)
- [ ] Database schema shown (30 sec)
- [ ] Workflow A demonstration (2 min)
- [ ] Workflow B demonstration (2 min)
- [ ] Workflow C demonstration (1 min)
- [ ] End-to-end demo (2 min)
- [ ] Email notification shown (30 sec)
- [ ] Conclusion (30 sec)

### Post-Recording
- [ ] Video edited (remove long waits)
- [ ] Annotations added
- [ ] Section labels added
- [ ] Quality verified (1080p minimum)
- [ ] Duration: 5-10 minutes
- [ ] Uploaded to video platform
- [ ] Link added to README

## Submission Checklist

### GitHub Repository
- [ ] Private repository created
- [ ] All code committed
- [ ] `.env` file NOT committed (in .gitignore)
- [ ] README.md includes setup instructions
- [ ] saurabh@clickpe.ai invited as collaborator
- [ ] harsh.srivastav@clickpe.ai invited as collaborator

### Required Files
- [ ] `README.md` - Main documentation
- [ ] `SETUP_GUIDE.md` - Detailed setup instructions
- [ ] `ARCHITECTURE.md` - Architecture explanation
- [ ] `serverless.yml` - AWS infrastructure
- [ ] `docker-compose.yml` - n8n setup
- [ ] `database/schema.sql` - Database schema
- [ ] `n8n-workflows/*.json` - All three workflows
- [ ] `frontend/index.html` - Upload interface
- [ ] `src/handlers/*.py` - Lambda functions
- [ ] `scripts/*.py` - Setup and utility scripts

### Deliverables
- [ ] GitHub repository with code
- [ ] Architecture diagram (in README)
- [ ] n8n workflow JSON files
- [ ] Demonstration video (5-10 min)
- [ ] Video link in README

## Final Verification

### Functionality
- [ ] CSV upload works end-to-end
- [ ] Users matched correctly
- [ ] Emails sent successfully
- [ ] All three n8n workflows operational
- [ ] Error handling works (invalid CSV, missing data)

### Performance
- [ ] Lambda executes within timeout
- [ ] Database queries optimized
- [ ] No unnecessary API calls
- [ ] Batch operations used where possible

### Security
- [ ] No secrets in repository
- [ ] Database not publicly accessible
- [ ] n8n protected with auth
- [ ] S3 bucket encrypted
- [ ] IAM roles follow least privilege

### Code Quality
- [ ] Code is clean and readable
- [ ] Functions are modular
- [ ] No hardcoded values
- [ ] Error handling implemented
- [ ] Logging added for debugging

### Design Quality
- [ ] Multi-stage filtering implemented
- [ ] AI used efficiently (optimization treasure hunt)
- [ ] Event-driven architecture
- [ ] Scalable design
- [ ] Professional email templates

## Evaluation Self-Assessment

### n8n Workflow Design & Automation (30 points)
- [ ] Three workflows implemented correctly
- [ ] Sophisticated node connections
- [ ] Optimization treasure hunt solved
- [ ] Robust error handling
- [ ] Creative use of n8n features

### Cloud Architecture & Integration (20 points)
- [ ] Serverless architecture implemented
- [ ] Event-driven CSV ingestion
- [ ] Secure AWS configuration
- [ ] n8n integrated with AWS
- [ ] Scalable design

### Backend Functionality & Code Quality (30 points)
- [ ] Data ingestion pipeline works
- [ ] Clean, modular code
- [ ] Well-commented code
- [ ] Proper error handling
- [ ] Database design is sound

### Documentation & Presentation (20 points)
- [ ] Clear architecture diagram
- [ ] Comprehensive README
- [ ] Detailed setup guide
- [ ] Quality video demonstration
- [ ] Professional presentation

## Post-Submission Cleanup (After Evaluation)

- [ ] Delete AWS resources (`serverless remove`)
- [ ] Stop n8n container (`docker-compose down`)
- [ ] Remove database snapshots
- [ ] Unverify SES email (if no longer needed)
- [ ] Remove SSM parameters
- [ ] Keep local copy of project for portfolio

---

**Estimated Time for Full Implementation**: 8-12 hours

**Recommended Order**:
1. Setup (2 hours)
2. Database & Lambda (2 hours)
3. n8n Workflows (3 hours)
4. Frontend (1 hour)
5. Testing (2 hours)
6. Documentation (1 hour)
7. Video (1 hour)

Good luck with your submission! 🚀
