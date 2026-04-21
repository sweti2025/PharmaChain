import json
from datetime import datetime

# Shared storage
drugs = []

def handler(request):
    """Handler for adding drugs endpoint"""
    try:
        # Parse request body
        if request.get('method') == 'POST':
            body = json.loads(request.get('body', '{}'))
            
            drug = {
                'batch_id': body.get('batch_id', f'DRUG-{len(drugs) + 1}'),
                'name': body.get('name', 'Unknown'),
                'manufacturer': body.get('manufacturer', 'Unknown'),
                'manufacture_date': body.get('manufacture_date', datetime.now().isoformat()),
                'expiry_date': body.get('expiry_date', datetime.now().isoformat())
            }
            
            drugs.append(drug)
            
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
