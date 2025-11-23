"""
Firebase Configuration Manager for PromptBuddy
Complete production-ready setup with Web SDK support
"""

import os
import json
from firebase_admin import credentials, firestore, auth as admin_auth, initialize_app

_db = None
_auth = None
_app = None

def get_firebase_web_config():
    """
    Get Firebase Web SDK configuration for client-side OAuth.
    Returns config dict if available, None otherwise.
    """
    # Try to load from secrets or environment
    web_config_path = os.path.join(os.path.dirname(__file__), "firebase_web_config.json")
    
    if os.path.exists(web_config_path):
        try:
            with open(web_config_path, 'r') as f:
                return json.load(f)
        except:
            pass
    
    # Try from environment variables
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and 'firebase_web' in st.secrets:
            return dict(st.secrets['firebase_web'])
    except:
        pass
    
    return None

def initialize_firebase():
    """
    Initialize Firebase Admin SDK.
    Returns: (db, auth, status, message)
    - status: 'connected' or 'local'
    - message: descriptive status message
    """
    global _db, _auth, _app
    
    # Return cached instance
    if _db is not None and _auth is not None:
        return _db, _auth, "connected", "Firebase connected"
    
    # Look for service account key
    key_path = os.path.join(os.path.dirname(__file__), "serviceAccountKey.json")
    
    if not os.path.exists(key_path):
        return None, None, "local", "Running in Local Mode. Firebase not configured."
    
    try:
        # Initialize Firebase Admin SDK
        cred = credentials.Certificate(key_path)
        if _app is None:
            _app = initialize_app(cred)
        
        _db = firestore.client()
        _auth = admin_auth
        
        return _db, _auth, "connected", "Firebase connected successfully"
        
    except Exception as e:
        return None, None, "local", f"Firebase initialization failed: {str(e)}"
