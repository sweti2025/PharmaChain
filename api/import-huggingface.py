import json
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def handler(request):
    """Handler for Hugging Face import endpoint"""
    try:
        # Simple in-memory storage
        if not hasattr(handler, 'drugs'):
            handler.drugs = []
        
        # Sample drug data (since datasets library not available on Vercel)
        sample_drugs = [
            {"name": "Aspirin", "manufacturer": "Bayer"},
            {"name": "Ibuprofen", "manufacturer": "Pfizer"},
            {"name": "Paracetamol", "manufacturer": "Johnson & Johnson"},
            {"name": "Metformin", "manufacturer": "Merck"},
            {"name": "Lisinopril", "manufacturer": "AstraZeneca"},
            {"name": "Atorvastatin", "manufacturer": "Pfizer"},
            {"name": "Omeprazole", "manufacturer": "AstraZeneca"},
            {"name": "Amoxicillin", "manufacturer": "GSK"},
            {"name": "Metoprolol", "manufacturer": "AstraZeneca"},
            {"name": "Losartan", "manufacturer": "Merck"}
        ]
        
        imported_count = 0
        for i, drug in enumerate(sample_drugs):
            drug_data = {
                'batch_id': f'SAMPLE-{drug["name"].replace(" ", "-").upper()}-{i:04d}',
                'name': drug['name'],
                'manufacturer': drug['manufacturer'],
                'manufacture_date': datetime.now().isoformat(),
                'expiry_date': (datetime.now().replace(year=datetime.now().year + 2)).isoformat()
            }
            handler.drugs.append(drug_data)
            imported_count += 1
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'imported_count': imported_count,
                'message': f'Successfully imported {imported_count} sample drugs'
            })
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
