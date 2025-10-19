"""
Firestore database configuration and initialization
"""
import os
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class MockFirestoreClient:
    """Mock Firestore client for development"""
    def collection(self, name):
        return MockCollection()
    
    def document(self, path):
        return MockDocument()

class MockCollection:
    """Mock Firestore collection"""
    def document(self, doc_id=None):
        return MockDocument()
    
    def add(self, data):
        return None, MockDocument()
    
    def get(self):
        return []
    
    def where(self, field, op, value):
        return self

class MockDocument:
    """Mock Firestore document"""
    def get(self):
        class MockDocSnapshot:
            exists = False
            def to_dict(self):
                return {}
        return MockDocSnapshot()
    
    def set(self, data):
        return None
    
    def update(self, data):
        return None
    
    def delete(self):
        return None

def initialize_firestore():
    """
    Initialize Firestore database connection.
    
    Returns:
        Firestore client instance
    """
    try:
        # Check if Firebase is already initialized
        if not firebase_admin._apps:
            # Option 1: Use service account key file
            service_account_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
            
            if service_account_path and os.path.exists(service_account_path):
                print(f"Initializing Firebase with service account: {service_account_path}")
                cred = credentials.Certificate(service_account_path)
                firebase_admin.initialize_app(cred)
            else:
                print("No service account found, trying default credentials...")
                project_id = os.getenv("FIREBASE_PROJECT_ID")
                if project_id:
                    firebase_admin.initialize_app(options={'projectId': project_id})
                else:
                    firebase_admin.initialize_app()
        
        client = firestore.client()
        print("✅ Firestore initialized successfully")
        return client
    except Exception as e:
        print(f"❌ Could not initialize Firestore: {e}")
        print("📝 To fix this:")
        print("   1. Download your Firebase service account key from Firebase Console")
        print("   2. Save it as 'firebase-service-account.json' in the backend directory")
        print("   3. Update FIREBASE_SERVICE_ACCOUNT_PATH in .env file")
        print("🔄 Using mock client for now...")
        return MockFirestoreClient()


# Global Firestore client instance
db = initialize_firestore()
