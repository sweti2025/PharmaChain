"""
Pharma Supply Chain Tracking System - Backend API
FastAPI application with Web3.py integration for blockchain interaction
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import os
import json
import sqlite3
from datetime import datetime, timezone
import qrcode
from io import BytesIO
import base64
from web3 import Web3
from eth_account import Account
import logging
import asyncio
from datasets import load_dataset

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Pharma Supply Chain API",
    description="Blockchain-based pharmaceutical drug tracking system",
    version="1.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
class Config:
    # Blockchain configuration
    INFURA_PROJECT_ID = os.getenv("INFURA_PROJECT_ID", "your-infura-project-id")
    SEPOLIA_RPC_URL = f"https://sepolia.infura.io/v3/{INFURA_PROJECT_ID}"
    CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS", "0x0000000000000000000000000000000000000000")  # Update after deployment
    PRIVATE_KEY = os.getenv("PRIVATE_KEY", "your-private-key")  # For demo purposes only
    CHAIN_ID = 11155111  # Sepolia testnet
    
    # Database configuration
    DB_PATH = "pharma_supply_chain.db"
    
    # Use in-memory storage for serverless environments
    USE_MEMORY_DB = os.getenv("USE_MEMORY_DB", "false").lower() == "true"

config = Config()

# In-memory storage for serverless environments
memory_db = {}

# Web3 setup
w3 = Web3(Web3.HTTPProvider(config.SEPOLIA_RPC_URL))

# Drug Interaction Checker
drug_interaction_model = None
MODEL_LOADED = False

def load_interaction_model():
    """Lazy load the drug interaction model when needed"""
    global drug_interaction_model, MODEL_LOADED
    if not MODEL_LOADED:
        try:
            from transformers import pipeline
            drug_interaction_model = pipeline("text-classification", model="distilbert-base-uncased")
            MODEL_LOADED = True
            logger.info("Drug interaction model loaded successfully")
        except Exception as e:
            logger.warning(f"Failed to load drug interaction model: {str(e)}")
            logger.info("Drug interaction checking will use rule-based fallback")
            MODEL_LOADED = False
    return drug_interaction_model

# Common drug interactions database (fallback if model not available)
KNOWN_INTERACTIONS = {
    "warfarin": ["aspirin", "ibuprofen", "naproxen"],
    "aspirin": ["warfarin", "ibuprofen", "naproxen"],
    "ibuprofen": ["warfarin", "aspirin", "naproxen"],
    "naproxen": ["warfarin", "aspirin", "ibuprofen"],
    "paracetamol": [],
    "metformin": ["cimetidine"],
    "lisinopril": ["potassium supplements"],
    "atorvastatin": ["grapefruit juice"],
}

def check_drug_interactions(drug_name: str, other_drugs: List[str] = None) -> List[dict]:
    """Check for drug interactions using model or fallback database"""
    interactions = []
    drug_name_lower = drug_name.lower()
    
    # Try to load the model if not already loaded
    model = load_interaction_model()
    
    if model:
        # Use the ML model for interaction checking
        for other_drug in (other_drugs or []):
            try:
                input_text = f"{drug_name} interacts with {other_drug}"
                result = model(input_text)
                if result[0]['score'] > 0.7:  # Threshold for interaction
                    interactions.append({
                        "drug": other_drug,
                        "severity": "high" if result[0]['score'] > 0.8 else "moderate",
                        "confidence": result[0]['score']
                    })
            except Exception as e:
                logger.error(f"Error checking interaction with {other_drug}: {str(e)}")
    else:
        # Use rule-based fallback
        if drug_name_lower in KNOWN_INTERACTIONS:
            known_interactions = KNOWN_INTERACTIONS[drug_name_lower]
            for interaction in known_interactions:
                if not other_drugs or interaction in [d.lower() for d in other_drugs]:
                    interactions.append({
                        "drug": interaction,
                        "severity": "moderate",
                        "confidence": 0.8
                    })
    
    return interactions

def import_drug_data_from_huggingface(dataset_name: str = "Fda/Drug-Labeling", max_records: int = 100) -> dict:
    """Import drug data from Hugging Face dataset"""
    try:
        logger.info(f"Loading dataset: {dataset_name}")
        
        # Initialize database only if not using memory DB
        if not config.USE_MEMORY_DB:
            init_database()
        
        # Try to load the specified dataset
        try:
            dataset = load_dataset(dataset_name, split="train")
            logger.info(f"Successfully loaded dataset: {dataset_name}")
        except Exception as e:
            logger.warning(f"Dataset {dataset_name} not found or not accessible: {str(e)}")
            logger.info("Using sample drug data instead")
            
            # Use sample drug data as fallback
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
            errors = []
            
            for i, drug in enumerate(sample_drugs[:max_records]):
                try:
                    drug_name = drug["name"]
                    manufacturer = drug["manufacturer"]
                    batch_id = f"SAMPLE-{drug_name.replace(' ', '-').upper()}-{i:04d}"
                    
                    current_date = datetime.now().isoformat()
                    expiry_date = (datetime.now().replace(year=datetime.now().year + 2)).isoformat()
                    
                    qr = qrcode.QRCode(version=1, box_size=10, border=5)
                    qr.add_data(batch_id)
                    qr.make(fit=True)
                    qr_image = qr.make_image(fill_color="black", back_color="white")
                    buffered = BytesIO()
                    qr_image.save(buffered, format="PNG")
                    qr_code = base64.b64encode(buffered.getvalue()).decode()
                    
                    if config.USE_MEMORY_DB:
                        memory_db[batch_id] = {
                            "batch_id": batch_id,
                            "drug_name": drug_name,
                            "manufacturer": manufacturer,
                            "manufacture_date": current_date,
                            "expiry_date": expiry_date,
                            "qr_code": qr_code
                        }
                    else:
                        conn = sqlite3.connect(config.DB_PATH)
                        cursor = conn.cursor()
                        cursor.execute("""
                            INSERT OR REPLACE INTO drug_batches (batch_id, drug_name, manufacturer, manufacture_date, expiry_date, qr_code)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (batch_id, drug_name, manufacturer, current_date, expiry_date, qr_code))
                        conn.commit()
                        conn.close()
                    
                    imported_count += 1
                    
                except Exception as e:
                    errors.append(f"Record {i}: {str(e)}")
                    logger.error(f"Error importing sample drug {i}: {str(e)}")
            
            logger.info(f"Successfully imported {imported_count} sample drugs")
            
            return {
                "success": True,
                "imported_count": imported_count,
                "errors": errors,
                "message": f"Successfully imported {imported_count} sample drugs (dataset not available)"
            }
        
        # Original dataset loading logic
        imported_count = 0
        errors = []
        
        for i, record in enumerate(dataset):
            if i >= max_records:
                break
            
            try:
                drug_name = record.get('drug_name', record.get('name', 'Unknown'))
                manufacturer = record.get('manufacturer', 'Unknown Manufacturer')
                batch_id = f"HF-{drug_name.replace(' ', '-').upper()}-{i:04d}"
                
                current_date = datetime.now().isoformat()
                expiry_date = (datetime.now().replace(year=datetime.now().year + 2)).isoformat()
                
                qr = qrcode.QRCode(version=1, box_size=10, border=5)
                qr.add_data(batch_id)
                qr.make(fit=True)
                qr_image = qr.make_image(fill_color="black", back_color="white")
                buffered = BytesIO()
                qr_image.save(buffered, format="PNG")
                qr_code = base64.b64encode(buffered.getvalue()).decode()
                
                if config.USE_MEMORY_DB:
                    memory_db[batch_id] = {
                        "batch_id": batch_id,
                        "drug_name": drug_name,
                        "manufacturer": manufacturer,
                        "manufacture_date": current_date,
                        "expiry_date": expiry_date,
                        "qr_code": qr_code
                    }
                else:
                    conn = sqlite3.connect(config.DB_PATH)
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT OR REPLACE INTO drug_batches (batch_id, drug_name, manufacturer, manufacture_date, expiry_date, qr_code)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (batch_id, drug_name, manufacturer, current_date, expiry_date, qr_code))
                    conn.commit()
                    conn.close()
                
                imported_count += 1
                
            except Exception as e:
                errors.append(f"Record {i}: {str(e)}")
                logger.error(f"Error importing record {i}: {str(e)}")
        
        logger.info(f"Successfully imported {imported_count} drugs from {dataset_name}")
        
        return {
            "success": True,
            "imported_count": imported_count,
            "errors": errors[:10],
            "message": f"Successfully imported {imported_count} drugs"
        }
        
    except Exception as e:
        logger.error(f"Error importing from Hugging Face: {str(e)}")
        return {
            "success": False,
            "imported_count": 0,
            "errors": [str(e)],
            "message": f"Failed to import: {str(e)}"
        }

# Contract ABI (simplified version - update after compilation)
CONTRACT_ABI = [
    {
        "inputs": [
            {"internalType": "string", "name": "_batchId", "type": "string"},
            {"internalType": "string", "name": "_name", "type": "string"},
            {"internalType": "string", "name": "_manufacturer", "type": "string"},
            {"internalType": "uint256", "name": "_manufactureDate", "type": "uint256"},
            {"internalType": "uint256", "name": "_expiryDate", "type": "uint256"}
        ],
        "name": "addDrug",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "string", "name": "_batchId", "type": "string"},
            {"internalType": "address", "name": "_newOwner", "type": "address"},
            {"internalType": "string", "name": "_newOwnerName", "type": "string"}
        ],
        "name": "transferDrug",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "string", "name": "_batchId", "type": "string"}
        ],
        "name": "getDrug",
        "outputs": [
            {"internalType": "string", "name": "name", "type": "string"},
            {"internalType": "string", "name": "manufacturer", "type": "string"},
            {"internalType": "uint256", "name": "manufactureDate", "type": "uint256"},
            {"internalType": "uint256", "name": "expiryDate", "type": "uint256"},
            {"internalType": "address", "name": "currentOwner", "type": "address"},
            {"internalType": "bool", "name": "isActive", "type": "bool"},
            {"internalType": "string[]", "name": "ownershipHistory", "type": "string[]"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "string", "name": "_batchId", "type": "string"}
        ],
        "name": "verifyDrug",
        "outputs": [
            {"internalType": "bool", "name": "isGenuine", "type": "bool"},
            {"internalType": "bool", "name": "isActive", "type": "bool"},
            {"internalType": "bool", "name": "isExpired", "type": "bool"},
            {"internalType": "string", "name": "drugName", "type": "string"},
            {"internalType": "string", "name": "currentOwnerName", "type": "string"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "address", "name": "_user", "type": "address"},
            {"internalType": "uint8", "name": "_role", "type": "uint8"}
        ],
        "name": "assignRole",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

# Initialize contract
contract = w3.eth.contract(
    address=config.CONTRACT_ADDRESS,
    abi=CONTRACT_ABI
)

# Database setup
def init_database():
    """Initialize SQLite database for off-chain data storage"""
    conn = sqlite3.connect(config.DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            address TEXT UNIQUE NOT NULL,
            role TEXT NOT NULL,
            name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS drug_batches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_id TEXT UNIQUE NOT NULL,
            drug_name TEXT NOT NULL,
            manufacturer TEXT NOT NULL,
            manufacture_date TIMESTAMP NOT NULL,
            expiry_date TIMESTAMP NOT NULL,
            qr_code TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()

# Pydantic models
class DrugCreate(BaseModel):
    batch_id: str
    name: str
    manufacturer: str
    manufacture_date: str  # ISO format
    expiry_date: str      # ISO format

class DrugTransfer(BaseModel):
    batch_id: str
    new_owner_address: str
    new_owner_name: str

class UserRole(BaseModel):
    address: str
    role: str  # "manufacturer", "distributor", "pharmacy"
    name: Optional[str] = None

class DrugVerification(BaseModel):
    batch_id: str

class DrugResponse(BaseModel):
    batch_id: str
    name: str
    manufacturer: str
    manufacture_date: str
    expiry_date: str
    current_owner: str
    is_active: bool
    ownership_history: List[str]
    qr_code: Optional[str] = None

class VerificationResponse(BaseModel):
    is_genuine: bool
    is_active: bool
    is_expired: bool
    drug_name: str
    current_owner: str
    ownership_history: List[str]
    qr_code: Optional[str] = None
    interactions: Optional[List[dict]] = None

class DrugInteractionCheck(BaseModel):
    drug_name: str
    other_drugs: Optional[List[str]] = None

class InteractionResponse(BaseModel):
    drug_name: str
    has_interactions: bool
    interactions: List[dict]
    message: str

class HuggingFaceImportRequest(BaseModel):
    dataset_name: str = "Fda/Drug-Labeling"
    max_records: int = 100

class HuggingFaceImportResponse(BaseModel):
    success: bool
    imported_count: int
    errors: List[str]
    message: str

# Helper functions
def get_account():
    """Get the account for transactions"""
    if config.PRIVATE_KEY == "your-private-key":
        # Generate a new account for demo
        account = Account.create()
        logger.warning(f"Using generated account: {account.address}")
        return account
    return Account.from_key(config.PRIVATE_KEY)

def generate_qr_code(batch_id: str) -> str:
    """Generate QR code for drug batch"""
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(f"DRUG:{batch_id}")
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    return f"data:image/png;base64,{img_str}"

def save_drug_to_db(drug_data: DrugCreate, qr_code: str):
    """Save drug information to local database or in-memory storage"""
    if config.USE_MEMORY_DB:
        # Use in-memory storage for serverless environments
        memory_db[drug_data.batch_id] = {
            "batch_id": drug_data.batch_id,
            "drug_name": drug_data.name,
            "manufacturer": drug_data.manufacturer,
            "manufacture_date": drug_data.manufacture_date,
            "expiry_date": drug_data.expiry_date,
            "qr_code": qr_code
        }
        logger.info(f"Saved drug {drug_data.batch_id} to memory storage")
        return
    
    conn = sqlite3.connect(config.DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO drug_batches 
            (batch_id, drug_name, manufacturer, manufacture_date, expiry_date, qr_code)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            drug_data.batch_id,
            drug_data.name,
            drug_data.manufacturer,
            drug_data.manufacture_date,
            drug_data.expiry_date,
            qr_code
        ))
        conn.commit()
    except sqlite3.IntegrityError:
        logger.warning(f"Drug batch {drug_data.batch_id} already exists in database")
    finally:
        conn.close()

def get_drug_from_db(batch_id: str) -> Optional[dict]:
    """Get drug information from local database or in-memory storage"""
    if config.USE_MEMORY_DB:
        # Use in-memory storage for serverless environments
        drug_data = memory_db.get(batch_id)
        if drug_data:
            return {
                "batch_id": drug_data["batch_id"],
                "name": drug_data["drug_name"],
                "manufacturer": drug_data["manufacturer"],
                "manufacture_date": drug_data["manufacture_date"],
                "expiry_date": drug_data["expiry_date"],
                "qr_code": drug_data["qr_code"]
            }
        return None
    
    conn = sqlite3.connect(config.DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT batch_id, drug_name, manufacturer, manufacture_date, expiry_date, qr_code
        FROM drug_batches WHERE batch_id = ?
    """, (batch_id,))
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return {
            "batch_id": result[0],
            "name": result[1],
            "manufacturer": result[2],
            "manufacture_date": result[3],
            "expiry_date": result[4],
            "qr_code": result[5]
        }
    return None

# API Routes
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_database()
    logger.info("Pharma Supply Chain API started")

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Pharma Supply Chain Tracking System API", "version": "1.0.0"}

@app.post("/api/drugs")
async def add_drug(drug: DrugCreate):
    """Add a new drug batch to the supply chain"""
    try:
        # Validate dates
        manufacture_date = datetime.fromisoformat(drug.manufacture_date.replace('Z', '+00:00'))
        expiry_date = datetime.fromisoformat(drug.expiry_date.replace('Z', '+00:00'))
        
        if expiry_date <= manufacture_date:
            raise HTTPException(
                status_code=400,
                detail="Expiry date must be after manufacture date"
            )
        
        # Generate QR code
        qr_code = generate_qr_code(drug.batch_id)
        
        # Save to local database
        save_drug_to_db(drug, qr_code)
        
        # For demo purposes, simulate blockchain transaction
        # In production, this would be an actual blockchain transaction
        logger.info(f"Adding drug {drug.batch_id} to blockchain")
        
        return {
            "message": "Drug added successfully",
            "batch_id": drug.batch_id,
            "qr_code": qr_code,
            "transaction_hash": "0x..."  # Simulated transaction hash
        }
        
    except Exception as e:
        logger.error(f"Error adding drug: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/drugs/transfer")
async def transfer_drug(transfer: DrugTransfer):
    """Transfer drug ownership in the supply chain"""
    try:
        # Validate new owner address
        if not w3.is_address(transfer.new_owner_address):
            raise HTTPException(
                status_code=400,
                detail="Invalid Ethereum address"
            )
        
        # Check if drug exists
        drug_data = get_drug_from_db(transfer.batch_id)
        if not drug_data:
            raise HTTPException(
                status_code=404,
                detail="Drug batch not found"
            )
        
        # For demo purposes, simulate blockchain transaction
        logger.info(f"Transferring drug {transfer.batch_id} to {transfer.new_owner_address}")
        
        return {
            "message": "Drug transferred successfully",
            "batch_id": transfer.batch_id,
            "new_owner": transfer.new_owner_name,
            "transaction_hash": "0x..."  # Simulated transaction hash
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error transferring drug: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/drugs/verify")
async def verify_drug(verification: DrugVerification) -> VerificationResponse:
    """Verify drug authenticity and get details"""
    try:
        # Get drug from local database
        drug_data = get_drug_from_db(verification.batch_id)
        
        if not drug_data:
            return VerificationResponse(
                is_genuine=False,
                is_active=False,
                is_expired=False,
                drug_name="Not Found",
                current_owner="Not Found",
                ownership_history=[]
            )
        
        # Check expiry
        expiry_date = datetime.fromisoformat(drug_data["expiry_date"].replace('Z', '+00:00'))
        is_expired = datetime.now(timezone.utc) > expiry_date
        
        # For demo purposes, simulate blockchain verification
        # In production, this would call the smart contract
        ownership_history = [
            drug_data["manufacturer"],
            "Distributor ABC",  # Simulated intermediate owners
            "Pharmacy XYZ"
        ]
        
        # Check for drug interactions
        interactions = check_drug_interactions(drug_data["name"])
        
        return VerificationResponse(
            is_genuine=True,
            is_active=True,
            is_expired=is_expired,
            drug_name=drug_data["name"],
            current_owner=ownership_history[-1],
            ownership_history=ownership_history,
            qr_code=drug_data["qr_code"],
            interactions=interactions if interactions else None
        )
        
    except Exception as e:
        logger.error(f"Error verifying drug: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/drugs/{batch_id}")
async def get_drug_details(batch_id: str) -> DrugResponse:
    """Get detailed information about a drug batch"""
    try:
        drug_data = get_drug_from_db(batch_id)
        
        if not drug_data:
            raise HTTPException(
                status_code=404,
                detail="Drug batch not found"
            )
        
        # Simulate ownership history
        ownership_history = [
            drug_data["manufacturer"],
            "Distributor ABC",
            "Pharmacy XYZ"
        ]
        
        return DrugResponse(
            batch_id=drug_data["batch_id"],
            name=drug_data["name"],
            manufacturer=drug_data["manufacturer"],
            manufacture_date=drug_data["manufacture_date"],
            expiry_date=drug_data["expiry_date"],
            current_owner="Pharmacy XYZ",  # Simulated current owner
            is_active=True,
            ownership_history=ownership_history,
            qr_code=drug_data["qr_code"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting drug details: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/drugs/check-interactions")
async def check_drug_interactions_endpoint(interaction_check: DrugInteractionCheck) -> InteractionResponse:
    """Check for drug interactions using ML model or rule-based fallback"""
    try:
        interactions = check_drug_interactions(
            interaction_check.drug_name,
            interaction_check.other_drugs
        )
        
        has_interactions = len(interactions) > 0
        
        message = "No drug interactions detected"
        if has_interactions:
            message = f"Found {len(interactions)} potential drug interaction(s)"
        
        return InteractionResponse(
            drug_name=interaction_check.drug_name,
            has_interactions=has_interactions,
            interactions=interactions,
            message=message
        )
        
    except Exception as e:
        logger.error(f"Error checking drug interactions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/drugs/import-huggingface")
async def import_drug_data(import_request: HuggingFaceImportRequest) -> HuggingFaceImportResponse:
    """Import drug data from Hugging Face dataset"""
    try:
        result = import_drug_data_from_huggingface(
            dataset_name=import_request.dataset_name,
            max_records=import_request.max_records
        )
        
        return HuggingFaceImportResponse(**result)
        
    except Exception as e:
        logger.error(f"Error importing drug data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/users/role")
async def assign_user_role(user_role: UserRole):
    """Assign role to a user"""
    try:
        # Validate Ethereum address
        if not w3.is_address(user_role.address):
            raise HTTPException(
                status_code=400,
                detail="Invalid Ethereum address"
            )
        
        # Validate role
        valid_roles = ["manufacturer", "distributor", "pharmacy"]
        if user_role.role.lower() not in valid_roles:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid role. Must be one of: {valid_roles}"
            )
        
        # Save to database
        conn = sqlite3.connect(config.DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO users (address, role, name)
            VALUES (?, ?, ?)
        """, (user_role.address, user_role.role.lower(), user_role.name))
        
        conn.commit()
        conn.close()
        
        return {
            "message": "User role assigned successfully",
            "address": user_role.address,
            "role": user_role.role
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error assigning user role: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/drugs")
async def list_drugs():
    """List all drug batches"""
    try:
        if config.USE_MEMORY_DB:
            # Use in-memory storage for serverless environments
            drugs = []
            for batch_id, drug_data in memory_db.items():
                drugs.append({
                    "batch_id": drug_data["batch_id"],
                    "name": drug_data["drug_name"],
                    "manufacturer": drug_data["manufacturer"],
                    "manufacture_date": drug_data["manufacture_date"],
                    "expiry_date": drug_data["expiry_date"]
                })
            return {"drugs": drugs}
        
        conn = sqlite3.connect(config.DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT batch_id, drug_name, manufacturer, manufacture_date, expiry_date
            FROM drug_batches
            ORDER BY created_at DESC
        """)
        
        results = cursor.fetchall()
        conn.close()
        
        drugs = []
        for row in results:
            drugs.append({
                "batch_id": row[0],
                "name": row[1],
                "manufacturer": row[2],
                "manufacture_date": row[3],
                "expiry_date": row[4]
            })
        
        return {"drugs": drugs}
        
    except Exception as e:
        logger.error(f"Error listing drugs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        conn = sqlite3.connect(config.DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        conn.close()
        
        # Check blockchain connection
        is_connected = w3.is_connected()
        
        return {
            "status": "healthy",
            "database": "connected",
            "blockchain": "connected" if is_connected else "disconnected",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
