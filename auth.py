"""
Authentication Module for PromptBuddy
OAuth Login (Google & Apple) only.
"""

import streamlit as st
import streamlit.components.v1 as components
import firebase_config
from firebase_admin import auth
import time
import json

def oauth_login():
    """Display OAuth Login Buttons"""
    st.subheader("🔐 Sign In")
    st.markdown("Choose your preferred sign-in method:")
    
    # GUEST MODE - Skip auth for testing
    if st.button("🚀 Continue as Guest", use_container_width=True, type="primary"):
        st.session_state.user = {
            "email": "guest@promptbuddy.app",
            "uid": "guest_user",
            "provider": "guest",
            "local": True,
            "display_name": "Guest User"
        }
        st.success("Welcome! You're using PromptBuddy in Guest Mode.")
        time.sleep(0.5)
        st.rerun()
    
    st.divider()
    st.caption("Or sign in with:")
    
    
    db, auth_client, status, msg = firebase_config.initialize_firebase()
    
    if status == "local":
        st.info("☁️ Running in Local Mode. Firebase not configured.")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔴 Continue with Google", use_container_width=True, type="primary"):
                st.session_state.user = {
                    "email": "demo@gmail.com",
                    "uid": "local_google_user",
                    "provider": "google.com",
                    "local": True,
                    "display_name": "Demo User"
                }
                st.success("Signed in with Google (Local Mode)")
                time.sleep(1)
                st.rerun()
        
        with col2:
            if st.button(" Continue with Apple", use_container_width=True):
                st.session_state.user = {
                    "email": "demo@icloud.com",
                    "uid": "local_apple_user",
                    "provider": "apple.com",
                    "local": True,
                    "display_name": "Demo User"
                }
                st.success("Signed in with Apple (Local Mode)")
                time.sleep(1)
                st.rerun()
    
    elif status == "connected":
        st.info("👉 Firebase OAuth requires Web SDK configuration.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔴 Continue with Google", use_container_width=True, type="primary"):
                st.warning("Configure Firebase Web SDK for production OAuth.")
        with col2:
            if st.button(" Continue with Apple", use_container_width=True):
                st.warning("Configure Firebase Web SDK for production OAuth.")

def logout():
    """Handle Logout"""
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        st.session_state.user = None
        st.session_state.prompt_history = []
        if "messages" in st.session_state:
            st.session_state.messages = []
        st.success("Logged out")
        time.sleep(1)
        st.rerun()

def auth_sidebar():
    """Render Auth Sidebar"""
    if 'user' not in st.session_state or st.session_state.user is None:
        oauth_login()
        st.divider()
        
        db, auth_client, status, msg = firebase_config.initialize_firebase()
        if status == "local":
            st.sidebar.info("☁️ **Cloud Sync Disabled**\\n\\nAdd `serviceAccountKey.json` to enable cloud features.")
        else:
            st.sidebar.success("☁️ **Cloud Sync Ready**")
            
    else:
        user = st.session_state.user
        st.sidebar.markdown(f"### 👤 {user.get('display_name', user['email'])}")
        st.sidebar.caption(user['email'])
        
        provider = user.get('provider', 'unknown')
        if 'google' in provider:
            st.sidebar.caption("🔴 Google Account")
        elif 'apple' in provider:
            st.sidebar.caption(" Apple Account")
        
        if user.get('local'):
            st.sidebar.caption("💻 Local Session")
        else:
            st.sidebar.caption("☁️ Cloud Session")
            
        st.divider()
        logout()
