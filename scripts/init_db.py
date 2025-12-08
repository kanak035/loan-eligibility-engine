#!/usr/bin/env python3
"""
Database initialization script.
Connects to RDS PostgreSQL and creates all necessary tables.
"""

import os
import psycopg2
from dotenv import load_dotenv
import sys

# Load environment variables
load_dotenv()

def get_db_config():
    """Get database configuration from environment variables."""
    return {
        'host': os.getenv('DB_HOST'),
        'port': os.getenv('DB_PORT', '5432'),
        'database': os.getenv('DB_NAME'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD')
    }

def init_database():
    """Initialize database with schema."""
    config = get_db_config()
    
    # Validate configuration
    missing = [k for k, v in config.items() if not v]
    if missing:
        print(f"Error: Missing configuration: {', '.join(missing)}")
        print("Please set the following environment variables:")
        print("DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD")
        sys.exit(1)
    
    try:
        print(f"Connecting to database at {config['host']}:{config['port']}...")
        conn = psycopg2.connect(**config)
        cursor = conn.cursor()
        
        # Read schema file
        schema_path = os.path.join(os.path.dirname(__file__), '..', 'database', 'schema.sql')
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
        
        print("Executing schema...")
        cursor.execute(schema_sql)
        conn.commit()
        
        print("✓ Database schema created successfully!")
        
        # Verify tables
        cursor.execute("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public' 
            ORDER BY tablename;
        """)
        tables = cursor.fetchall()
        
        print("\nCreated tables:")
        for table in tables:
            print(f"  - {table[0]}")
        
        # Display sample data counts
        cursor.execute("SELECT COUNT(*) FROM loan_products;")
        product_count = cursor.fetchone()[0]
        print(f"\nSample loan products inserted: {product_count}")
        
        cursor.close()
        conn.close()
        
        print("\n✓ Database initialization completed successfully!")
        
    except psycopg2.Error as e:
        print(f"Database error: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("Error: schema.sql file not found")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    init_database()
