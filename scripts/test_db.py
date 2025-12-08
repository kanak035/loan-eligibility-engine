#!/usr/bin/env python3
"""
Test database connection.
"""

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def test_connection():
    """Test database connection."""
    config = {
        'host': os.getenv('DB_HOST'),
        'port': os.getenv('DB_PORT', '5432'),
        'database': os.getenv('DB_NAME'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD')
    }
    
    try:
        print(f"Testing connection to {config['host']}:{config['port']}...")
        conn = psycopg2.connect(**config)
        cursor = conn.cursor()
        
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✓ Connected successfully!")
        print(f"PostgreSQL version: {version[0]}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"✗ Connection failed: {e}")

if __name__ == '__main__':
    test_connection()
