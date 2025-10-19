"""
Firestore database configuration and initialization
"""
import os
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def initialize_firestore():
    """
    Initialize Firestore database connection.
    
    Returns:
        Firestore client instance
    """
    # Check if Firebase is already initialized
    if not firebase_admin._apps:
        # Option 1: Use service account key file
        service_account_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
        
        if service_account_path and os.path.exists(service_account_path):
            cred = credentials.Certificate(service_account_path)
            firebase_admin.initialize_app(cred)
        else:
            # Option 2: Use default credentials (for Cloud Run, App Engine, etc.)
            firebase_admin.initialize_app()
    
    return firestore.client()


# Global Firestore client instance
db = initialize_firestore()
