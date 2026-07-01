import os
import requests
from dotenv import load_dotenv

load_dotenv()

FLUXBASE_URL = 'https://fluxbase.vercel.app/api/execute-sql'
API_KEY = os.getenv('FLUXBASE_API_KEY')
PROJECT_ID = os.getenv('FLUXBASE_PROJECT_ID')

def run_query(sql: str):
    if not API_KEY or not PROJECT_ID:
        raise Exception("Fluxbase credentials not found in environment variables.")

    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }
    payload = {'projectId': PROJECT_ID, 'query': sql}
    
    resp = requests.post(FLUXBASE_URL, json=payload, headers=headers)
    data = resp.json()
    
    if not data.get('success'):
        error_msg = data.get('error', {}).get('message', 'Unknown error')
        raise Exception(f"Fluxbase Error: {error_msg}")
    
    # DDL statements (CREATE, ALTER, DROP) might return {success: true, result: {message: "..."}} with no rows
    result = data.get('result', {})
    return result.get('rows', [])

def get_user_by_email(email: str):
    # Security Note: in a real application, be careful of SQL injection! 
    # Fluxbase doesn't natively mention parameterized queries in the simplified PDF, 
    # but we should escape single quotes in email.
    escaped_email = email.replace("'", "''")
    query = f"SELECT * FROM users WHERE email = '{escaped_email}'"
    rows = run_query(query)
    if rows and len(rows) > 0:
        return rows[0]
    return None

def create_user(name: str, email: str, password_hash: str):
    escaped_name = name.replace("'", "''")
    escaped_email = email.replace("'", "''")
    escaped_hash = password_hash.replace("'", "''")
    
    query = f"INSERT INTO users (name, email, password_hash) VALUES ('{escaped_name}', '{escaped_email}', '{escaped_hash}')"
    return run_query(query)
