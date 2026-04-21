from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
import os

# Add parent directory to path to import backend
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the FastAPI app from backend
from backend.app import app

# Vercel serverless function handler
from mangum import Mangum

# Create ASGI handler for Vercel
handler = Mangum(app, lifespan="off")
