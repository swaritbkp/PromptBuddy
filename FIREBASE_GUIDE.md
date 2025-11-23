# Firebase Integration Guide for PromptBuddy

## Overview

This guide covers integrating Firebase into PromptBuddy for user authentication, cloud storage of prompts/history, and real-time sync across devices.

---

## Phase 1: Setup Firebase Project

### 1.1 Create Firebase Project
```bash
# Visit https://console.firebase.google.com/
# Click "Add Project"
# Project Name: PromptBuddy
# Enable Google Analytics (optional)
```

### 1.2 Add Web App
```
1. In Firebase Console → Project Settings
2. Under "Your apps" → Click Web icon (</>) 
3. Register app: "PromptBuddy Web"
4. Copy the Firebase config object
```

### 1.3 Enable Services
```
Firebase Console → Build menu:
✅ Authentication (Email/Password, Google Sign-In)
✅ Firestore Database (for prompts, history, templates)
✅ Storage (for uploaded images/documents)
```

---

## Phase 2: Install Dependencies

### 2.1 Update `requirements.txt`
```txt
streamlit
google-generativeai
plotly
PyPDF2
requests
pillow
pandas
textstat
pyperclip
firebase-admin  # NEW
streamlit-firebase-auth  # NEW (if using pre-built auth)
```

### 2.2 Install
```bash
pip install firebase-admin streamlit-firebase-auth
```

---

## Phase 3: Firebase Configuration

### 3.1 Download Service Account Key
```
Firebase Console → Project Settings → Service Accounts
→ "Generate new private key"
→ Save as firebase-credentials.json in project root
→ Add to .gitignore!
```

### 3.2 Create `firebase_config.py`
```python
import firebase_admin
from firebase_admin import credentials, firestore, auth, storage
import streamlit as st

def initialize_firebase():
    """Initialize Firebase Admin SDK"""
    if not firebase_admin._apps:
        # Load credentials from Streamlit secrets in production
        # or from file locally
        try:
            # Production (Streamlit Cloud)
            cred_dict = dict(st.secrets["firebase"])
            cred = credentials.Certificate(cred_dict)
        except:
            # Local development
            cred = credentials.Certificate("firebase-credentials.json")
        
        firebase_admin.initialize_app(cred, {
            'storageBucket': 'promptbuddy.appspot.com'  # Your bucket name
        })
    
    return {
        'db': firestore.client(),
        'storage': storage.bucket()
    }

# Global Firebase instances
firebase = initialize_firebase()
db = firebase['db']
bucket = firebase['storage']
```

### 3.3 Add Firebase Secrets to `.streamlit/secrets.toml`
```toml
GEMINI_API_KEY = "your-key"

[firebase]
type = "service_account"
project_id = "promptbuddy-xxxxx"
private_key_id = "xxxxx"
private_key = "-----BEGIN PRIVATE KEY-----\nxxxxx\n-----END PRIVATE KEY-----\n"
client_email = "firebase-adminsdk-xxxxx@promptbuddy-xxxxx.iam.gserviceaccount.com"
client_id = "xxxxx"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-xxxxx%40promptbuddy-xxxxx.iam.gserviceaccount.com"
```

---

## Phase 4: Implement Authentication

### 4.1 Create `auth.py`
```python
import streamlit as st
from firebase_admin import auth as firebase_auth
from firebase_config import db
import datetime

def show_login_page():
    """Display login/signup interface"""
    st.title("🔐 Welcome to PromptBuddy")
    
    tab1, tab2 = st.tabs(["Sign In", "Sign Up"])
    
    with tab1:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Sign In"):
            try:
                # Verify credentials (client-side, use Firebase Auth REST API)
                # Or use streamlit-firebase-auth library
                user = verify_user(email, password)
                st.session_state.user = user
                st.rerun()
            except Exception as e:
                st.error(f"Login failed: {e}")
    
    with tab2:
        email = st.text_input("Email", key="signup_email")
        password = st.text_input("Password", type="password", key="signup_password")
        display_name = st.text_input("Display Name")
        
        if st.button("Sign Up"):
            try:
                user = firebase_auth.create_user(
                    email=email,
                    password=password,
                    display_name=display_name
                )
                
                # Create user document in Firestore
                db.collection('users').document(user.uid).set({
                    'email': email,
                    'display_name': display_name,
                    'created_at': datetime.datetime.now(),
                    'prompt_count': 0
                })
                
                st.success("Account created! Please sign in.")
            except Exception as e:
                st.error(f"Signup failed: {e}")

def verify_user(email, password):
    """Verify user credentials (simplified - use Firebase Auth SDK properly)"""
    # In production, use Firebase Auth REST API or streamlit-firebase-auth
    # This is a placeholder
    pass

def logout():
    """Log out current user"""
    if 'user' in st.session_state:
        del st.session_state.user
    st.rerun()
```

### 4.2 Update `app.py` Main
```python
import streamlit as st
from auth import show_login_page, logout
from firebase_config import db

# Check if user is logged in
if 'user' not in st.session_state:
    show_login_page()
    st.stop()

# User is logged in - show app
user_id = st.session_state.user['uid']

# Add logout button in sidebar
with st.sidebar:
    st.write(f"👤 {st.session_state.user.get('display_name', 'User')}")
    if st.button("Logout"):
        logout()
    st.divider()
    # Rest of sidebar...
```

---

## Phase 5: Firestore Data Structure

### 5.1 Collections Schema

```
users/
  {user_id}/
    - email: string
    - display_name: string
    - created_at: timestamp
    - prompt_count: number
    
prompts/
  {prompt_id}/
    - user_id: string
    - content: string
    - model: string
    - score: number
    - created_at: timestamp
    - updated_at: timestamp
    - category: string
    - tags: array
    
history/
  {user_id}/
    entries/
      {entry_id}/
        - prompt: string
        - output: string
        - model: string
        - timestamp: timestamp
        - latency: number
        - score: number

templates/
  {template_id}/
    - name: string
    - category: string
    - content: string
    - is_public: boolean
    - created_by: string (user_id)
    - downloads: number
```

### 5.2 CRUD Operations

```python
from firebase_config import db
import datetime

# CREATE
def save_prompt_to_cloud(user_id, prompt_data):
    """Save prompt to Firestore"""
    doc_ref = db.collection('prompts').document()
    doc_ref.set({
        'user_id': user_id,
        'content': prompt_data['content'],
        'model': prompt_data.get('model', 'gemini-3-pro-preview'),
        'score': prompt_data.get('score', 0),
        'created_at': datetime.datetime.now(),
        'updated_at': datetime.datetime.now()
    })
    return doc_ref.id

# READ
def get_user_prompts(user_id, limit=50):
    """Fetch user's prompts from Firestore"""
    prompts = db.collection('prompts')\
        .where('user_id', '==', user_id)\
        .order_by('created_at', direction='DESCENDING')\
        .limit(limit)\
        .stream()
    
    return [{'id': p.id, **p.to_dict()} for p in prompts]

# UPDATE
def update_prompt_score(prompt_id, new_score):
    """Update prompt score"""
    db.collection('prompts').document(prompt_id).update({
        'score': new_score,
        'updated_at': datetime.datetime.now()
    })

# DELETE
def delete_prompt(prompt_id):
    """Delete a prompt"""
    db.collection('prompts').document(prompt_id).delete()
```

---

## Phase 6: Real-Time Sync

### 6.1 Listen to Changes
```python
import streamlit as st
from firebase_config import db

def sync_history_realtime(user_id):
    """Watch for real-time updates"""
    # Create a callback for document changes
    def on_snapshot(doc_snapshot, changes, read_time):
        for change in changes:
            if change.type.name == 'ADDED':
                st.session_state.history.append(change.document.to_dict())
            elif change.type.name == 'MODIFIED':
                # Update existing entry
                pass
            elif change.type.name == 'REMOVED':
                # Remove from session state
                pass
        st.rerun()
    
    # Watch collection
    query = db.collection('history').document(user_id).collection('entries')
    query_watch = query.on_snapshot(on_snapshot)
    
    return query_watch
```

---

## Phase 7: File Storage (Images/Docs)

### 7.1 Upload Files
```python
from firebase_config import bucket
import uuid

def upload_file_to_storage(file, user_id):
    """Upload file to Firebase Storage"""
    file_id = str(uuid.uuid4())
    blob = bucket.blob(f'users/{user_id}/uploads/{file_id}_{file.name}')
    
    blob.upload_from_string(
        file.read(),
        content_type=file.type
    )
    
    # Make public or get signed URL
    blob.make_public()
    return blob.public_url
```

---

## Phase 8: Security Rules

### 8.1 Firestore Rules
```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Users can only read/write their own data
    match /prompts/{promptId} {
      allow read, write: if request.auth != null && 
                            resource.data.user_id == request.auth.uid;
    }
    
    match /history/{userId}/entries/{entryId} {
      allow read, write: if request.auth != null && 
                            userId == request.auth.uid;
    }
    
    // Public templates
    match /templates/{templateId} {
      allow read: if true;
      allow write: if request.auth != null;
    }
  }
}
```

### 8.2 Storage Rules
```javascript
rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {
    match /users/{userId}/{allPaths=**} {
      allow read, write: if request.auth != null && 
                           request.auth.uid == userId;
    }
  }
}
```

---

## Phase 9: Migration from Local to Cloud

### 9.1 Migrate Existing History
```python
def migrate_local_to_cloud(user_id):
    """Migrate history.json to Firestore"""
    import json
    
    try:
        with open('history.json', 'r') as f:
            local_history = json.load(f)
        
        batch = db.batch()
        history_ref = db.collection('history').document(user_id).collection('entries')
        
        for entry in local_history:
            doc_ref = history_ref.document()
            batch.set(doc_ref, entry)
        
        batch.commit()
        st.success(f"Migrated {len(local_history)} prompts to cloud!")
    except Exception as e:
        st.error(f"Migration failed: {e}")
```

---

## Phase 10: Deployment Checklist

### 10.1 Streamlit Cloud Setup
```
1. Push code to GitHub
2. Connect Streamlit Cloud to repo
3. Add secrets in Streamlit Cloud dashboard:
   - Copy entire .streamlit/secrets.toml content
4. Deploy!
```

### 10.2 Environment Variables
```python
import os

# Detect environment
IS_PRODUCTION = os.getenv("STREAMLIT_SHARING_MODE") is not None

if IS_PRODUCTION:
    # Use Streamlit secrets
    firebase_config = dict(st.secrets["firebase"])
else:
    # Use local file
    firebase_config = "firebase-credentials.json"
```

---

## Benefits of Firebase Integration

✅ **User Authentication**: Secure login/signup
✅ **Cloud Storage**: Access prompts from any device
✅ **Real-time Sync**: Collaborate or sync across sessions
✅ **Scalability**: Firebase handles millions of users
✅ **Analytics**: Track user engagement
✅ **Free Tier**: Generous limits for small projects

---

## Cost Estimate (Firebase Free Tier)

- **Authentication**: 10K verifications/month
- **Firestore**: 1GB storage, 50K reads/day, 20K writes/day
- **Storage**: 5GB
- **Functions**: 125K invocations/month

For PromptBuddy with ~100-500 users, free tier is sufficient!

---

## Next Steps

1. **Phase 5**: Implement Firebase authentication
2. **Phase 6**: Migrate history to Firestore
3. **Phase 7**: Add multi-user features (share prompts, leaderboards)
4. **Phase 8**: Real-time collaboration mode

Let me know when you want to start Firebase integration! 🚀
