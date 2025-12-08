"""
Lambda function to trigger n8n webhooks.
Can be invoked by other Lambda functions or scheduled events.
"""

import json
import os
import logging
import requests
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    """
    Trigger n8n webhook with custom payload.
    
    Args:
        event: Contains webhook_url and payload
        context: Lambda context
    """
    try:
        webhook_url = event.get('webhook_url') or os.environ.get('N8N_WEBHOOK_URL')
        
        if not webhook_url:
            raise ValueError('No webhook URL provided')
        
        payload = event.get('payload', {})
        payload['timestamp'] = datetime.now().isoformat()
        payload['source'] = 'lambda'
        
        logger.info(f'Triggering webhook: {webhook_url}')
        
        response = requests.post(
            webhook_url,
            json=payload,
            timeout=30,
            headers={'Content-Type': 'application/json'}
        )
        
        response.raise_for_status()
        
        logger.info(f'Webhook triggered successfully: {response.status_code}')
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Webhook triggered successfully',
                'response_code': response.status_code,
                'response_body': response.text
            })
        }
        
    except requests.exceptions.RequestException as e:
        logger.error(f'Error triggering webhook: {str(e)}')
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Failed to trigger webhook',
                'message': str(e)
            })
        }
        
    except Exception as e:
        logger.error(f'Unexpected error: {str(e)}')
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        }
