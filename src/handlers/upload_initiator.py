"""
Lambda function to generate pre-signed S3 URLs for CSV uploads.
This enables direct browser-to-S3 uploads, bypassing API Gateway size limits.
"""

import json
import os
import boto3
from datetime import datetime
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client('s3')

def handler(event, context):
    """
    Generate a pre-signed URL for uploading CSV files to S3.
    
    Args:
        event: API Gateway event containing filename in body
        context: Lambda context
        
    Returns:
        Pre-signed URL and upload metadata
    """
    try:
        # Parse request body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})
        
        filename = body.get('filename', f'upload_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
        
        # Validate filename
        if not filename.endswith('.csv'):
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Credentials': True
                },
                'body': json.dumps({
                    'error': 'Filename must end with .csv'
                })
            }
        
        bucket_name = os.environ['CSV_BUCKET_NAME']
        
        # Generate unique key with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        object_key = f'uploads/{timestamp}_{filename}'
        
        # Generate pre-signed URL for PUT operation
        presigned_url = s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': bucket_name,
                'Key': object_key,
                'ContentType': 'text/csv'
            },
            ExpiresIn=3600  # URL valid for 1 hour
        )
        
        logger.info(f'Generated pre-signed URL for {object_key}')
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Credentials': True,
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'uploadUrl': presigned_url,
                'objectKey': object_key,
                'bucket': bucket_name,
                'expiresIn': 3600
            })
        }
        
    except Exception as e:
        logger.error(f'Error generating pre-signed URL: {str(e)}')
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Credentials': True
            },
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        }
