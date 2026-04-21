#!/usr/bin/env python3
"""
Deploy Pharma Supply Chain Smart Contract to Sepolia Testnet
"""

import os
import json
from web3 import Web3
from web3.middleware import geth_poa_middleware
from solcx import compile_standard, install_solc
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
INFURA_PROJECT_ID = os.getenv("INFURA_PROJECT_ID", "your-infura-project-id")
PRIVATE_KEY = os.getenv("PRIVATE_KEY", "your-private-key")
SEPOLIA_RPC_URL = f"https://sepolia.infura.io/v3/{INFURA_PROJECT_ID}"
CHAIN_ID = 11155111  # Sepolia testnet

def compile_contract():
    """Compile the Solidity contract"""
    logger.info("Compiling smart contract...")
    
    # Install Solidity compiler
    install_solc("0.8.19")
    
    # Read contract source
    with open("../contracts/PharmaSupplyChain.sol", "r") as f:
        contract_source = f.read()
    
    # Compile contract
    compiled_sol = compile_standard(
        {
            "language": "Solidity",
            "sources": {
                "PharmaSupplyChain.sol": {
                    "content": contract_source
                }
            },
            "settings": {
                "outputSelection": {
                    "*": {
                        "*": ["abi", "metadata", "evm.bytecode", "evm.sourceMap"]
                    }
                }
            }
        },
        solc_version="0.8.19"
    )
    
    # Save compiled contract
    with open("compiled_contract.json", "w") as f:
        json.dump(compiled_sol, f, indent=2)
    
    logger.info("Contract compiled successfully")
    return compiled_sol

def deploy_contract():
    """Deploy the compiled contract to Sepolia"""
    logger.info("Deploying contract to Sepolia testnet...")
    
    # Connect to Sepolia
    w3 = Web3(Web3.HTTPProvider(SEPOLIA_RPC_URL))
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    
    if not w3.is_connected():
        raise Exception("Failed to connect to Sepolia network")
    
    # Get account
    account = w3.eth.account.from_key(PRIVATE_KEY)
    logger.info(f"Deploying from account: {account.address}")
    
    # Check balance
    balance = w3.eth.get_balance(account.address)
    logger.info(f"Account balance: {w3.from_wei(balance, 'ether')} ETH")
    
    if balance < 0.01:  # Minimum 0.01 ETH for deployment
        raise Exception("Insufficient balance for deployment")
    
    # Compile contract
    compiled_sol = compile_contract()
    
    # Get contract data
    contract_interface = compiled_sol["contracts"]["PharmaSupplyChain.sol"]["PharmaSupplyChain"]
    bytecode = contract_interface["evm"]["bytecode"]["object"]
    abi = contract_interface["abi"]
    
    # Create contract instance
    contract = w3.eth.contract(abi=abi, bytecode=bytecode)
    
    # Build transaction
    nonce = w3.eth.get_transaction_count(account.address)
    transaction = contract.constructor().build_transaction({
        "chainId": CHAIN_ID,
        "gasPrice": w3.eth.gas_price,
        "from": account.address,
        "nonce": nonce
    })
    
    # Estimate gas
    gas_estimate = w3.eth.estimate_gas(transaction)
    logger.info(f"Estimated gas: {gas_estimate}")
    
    # Sign and send transaction
    signed_txn = w3.eth.account.sign_transaction(transaction, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
    
    logger.info(f"Transaction sent: {tx_hash.hex()}")
    logger.info("Waiting for transaction receipt...")
    
    # Wait for receipt
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    
    if receipt.status == 1:
        contract_address = receipt.contractAddress
        logger.info(f"Contract deployed successfully at: {contract_address}")
        
        # Save deployment info
        deployment_info = {
            "contract_address": contract_address,
            "transaction_hash": tx_hash.hex(),
            "block_number": receipt.blockNumber,
            "gas_used": receipt.gasUsed,
            "abi": abi
        }
        
        with open("deployment_info.json", "w") as f:
            json.dump(deployment_info, f, indent=2)
        
        logger.info("Deployment info saved to deployment_info.json")
        return contract_address
    else:
        raise Exception("Contract deployment failed")

def update_backend_config(contract_address):
    """Update backend configuration with new contract address"""
    env_file = "../backend/.env"
    
    if not os.path.exists(env_file):
        # Create .env from example
        with open("../backend/.env.example", "r") as example:
            content = example.read()
        
        with open(env_file, "w") as env:
            env.write(content)
    
    # Update contract address
    with open(env_file, "r") as f:
        lines = f.readlines()
    
    with open(env_file, "w") as f:
        for line in lines:
            if line.startswith("CONTRACT_ADDRESS="):
                f.write(f"CONTRACT_ADDRESS={contract_address}\n")
            else:
                f.write(line)
    
    logger.info(f"Updated CONTRACT_ADDRESS in {env_file}")

if __name__ == "__main__":
    try:
        # Check environment variables
        if INFURA_PROJECT_ID == "your-infura-project-id":
            logger.error("Please set INFURA_PROJECT_ID environment variable")
            exit(1)
        
        if PRIVATE_KEY == "your-private-key":
            logger.error("Please set PRIVATE_KEY environment variable")
            exit(1)
        
        # Deploy contract
        contract_address = deploy_contract()
        
        # Update backend configuration
        update_backend_config(contract_address)
        
        logger.info("🎉 Contract deployment completed successfully!")
        logger.info(f"Contract Address: {contract_address}")
        logger.info("Next steps:")
        logger.info("1. Update frontend to use the new contract address")
        logger.info("2. Start the backend server")
        logger.info("3. Open the frontend application")
        
    except Exception as e:
        logger.error(f"Deployment failed: {str(e)}")
        exit(1)
