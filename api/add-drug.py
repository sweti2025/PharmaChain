import json
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def handler(request):
    """Handler for adding drugs endpoint"""
    try:
        # Parse request body
        if request.get('method') == 'POST':
            body = json.loads(request.get('body', '{}'))
            
            # Simple in-memory storage
            if not hasattr(handler, 'drugs'):
                handler.drugs = []
            
            drug = {
                'batch_id': body.get('batch_id', f'DRUG-{len(handler.drugs) + 1}'),
                'name': body.get('name', 'Unknown'),
                'manufacturer': body.get('manufacturer', 'Unknown'),
                'manufacture_date': body.get('manufacture_date', datetime.now().isoformat()),
                'expiry_date': body.get('expiry_date', datetime.now().isoformat())
            }
            
            handler.drugs.append(drug)
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'message': 'Drug added successfully', 'drug': drug})
            }
        
        return {
            'statusCode': 405,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'Method not allowed'})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': str(e)})
        }
