"""
Lambda function to process uploaded CSV files from S3.
Triggered by S3 event when a new CSV is uploaded.
Parses CSV, validates data, and stores in RDS PostgreSQL.
"""

import json
import os
import boto3
import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch
import logging
from io import StringIO
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client('s3')

# Database connection parameters
DB_CONFIG = {
    'host': os.environ['DB_HOST'],
    'port': os.environ['DB_PORT'],
    'database': os.environ['DB_NAME'],
    'user': os.environ['DB_USER'],
    'password': os.environ['DB_PASSWORD']
}

def get_db_connection():
    """Create database connection."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        logger.error(f'Database connection error: {str(e)}')
        raise

def validate_csv_data(df):
    """
    Validate CSV data structure and content.
    
    Required columns:
    - user_id (optional - will be generated if missing)
    - email
    - monthly_income
    - credit_score
    - employment_status
    - age
    """
    required_columns = ['email', 'monthly_income', 'credit_score', 'employment_status', 'age']
    
    # Check for required columns
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f'Missing required columns: {missing_columns}')
    
    # Validate data types and ranges
    errors = []
    
    # Email validation (basic)
    if not df['email'].str.contains('@').all():
        errors.append('Invalid email addresses found')
    
    # Monthly income validation
    if (df['monthly_income'] < 0).any():
        errors.append('Monthly income cannot be negative')
    
    # Credit score validation (300-850 range)
    if ((df['credit_score'] < 300) | (df['credit_score'] > 850)).any():
        errors.append('Credit score must be between 300 and 850')
    
    # Age validation
    if ((df['age'] < 18) | (df['age'] > 100)).any():
        errors.append('Age must be between 18 and 100')
    
    if errors:
        raise ValueError(f'Data validation errors: {"; ".join(errors)}')
    
    return True

def insert_users_batch(conn, df):
    """
    Insert users from DataFrame into database using batch insert.
    
    Args:
        conn: Database connection
        df: Pandas DataFrame with user data
        
    Returns:
        Number of rows inserted
    """
    cursor = conn.cursor()
    
    try:
        # Prepare data for insertion
        insert_query = """
            INSERT INTO users (email, monthly_income, credit_score, employment_status, age)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (email) DO UPDATE SET
                monthly_income = EXCLUDED.monthly_income,
                credit_score = EXCLUDED.credit_score,
                employment_status = EXCLUDED.employment_status,
                age = EXCLUDED.age,
                created_at = CURRENT_TIMESTAMP
            RETURNING user_id;
        """
        
        # Convert DataFrame to list of tuples
        data = [
            (
                row['email'],
                float(row['monthly_income']),
                int(row['credit_score']),
                row['employment_status'],
                int(row['age'])
            )
            for _, row in df.iterrows()
        ]
        
        # Batch insert
        execute_batch(cursor, insert_query, data, page_size=100)
        conn.commit()
        
        rows_affected = cursor.rowcount
        logger.info(f'Inserted/Updated {rows_affected} users')
        
        return rows_affected
        
    except Exception as e:
        conn.rollback()
        logger.error(f'Error inserting users: {str(e)}')
        raise
    finally:
        cursor.close()

def trigger_n8n_webhook(user_count):
    """
    Trigger n8n workflow via webhook after successful CSV processing.
    
    Args:
        user_count: Number of users processed
    """
    webhook_url = os.environ.get('N8N_WEBHOOK_URL')
    
    if not webhook_url:
        logger.warning('N8N_WEBHOOK_URL not configured, skipping webhook trigger')
        return
    
    try:
        import requests
        
        payload = {
            'event': 'csv_processed',
            'user_count': user_count,
            'timestamp': datetime.now().isoformat(),
            'trigger_matching': True
        }
        
        response = requests.post(webhook_url, json=payload, timeout=10)
        response.raise_for_status()
        
        logger.info(f'Successfully triggered n8n webhook: {response.status_code}')
        
    except Exception as e:
        logger.error(f'Error triggering n8n webhook: {str(e)}')
        # Don't raise - webhook failure shouldn't fail the entire process

def handler(event, context):
    """
    Process CSV file upload from S3 event.
    
    Args:
        event: S3 event notification
        context: Lambda context
    """
    try:
        # Extract S3 event details
        for record in event['Records']:
            bucket_name = record['s3']['bucket']['name']
            object_key = record['s3']['object']['key']
            
            logger.info(f'Processing file: s3://{bucket_name}/{object_key}')
            
            # Download CSV from S3
            response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
            csv_content = response['Body'].read().decode('utf-8')
            
            # Parse CSV with pandas
            df = pd.read_csv(StringIO(csv_content))
            logger.info(f'Loaded {len(df)} rows from CSV')
            
            # Validate data
            validate_csv_data(df)
            logger.info('CSV data validation passed')
            
            # Connect to database
            conn = get_db_connection()
            
            # Insert users
            rows_inserted = insert_users_batch(conn, df)
            
            # Close connection
            conn.close()
            
            # Trigger n8n webhook for matching workflow
            trigger_n8n_webhook(rows_inserted)
            
            logger.info(f'Successfully processed {rows_inserted} users from {object_key}')
            
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'CSV processed successfully',
                'rows_processed': rows_inserted
            })
        }
        
    except ValueError as ve:
        logger.error(f'Validation error: {str(ve)}')
        return {
            'statusCode': 400,
            'body': json.dumps({
                'error': 'Data validation failed',
                'message': str(ve)
            })
        }
        
    except Exception as e:
        logger.error(f'Error processing CSV: {str(e)}')
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        }
