"""
UI Components for PromptBuddy
Handles styling, sidebar, and common UI elements.
"""

import streamlit as st
import os
import utils
import time
import auth
import firebase_config
import json

def render_custom_css():
    """Render the custom CSS for the application"""
    st.markdown("""
    <style>
        /* Global Variables for Premium Theme */
        :root {
            --primary-color: #800020;
            --secondary-color: #B22222;
            --accent-color: #FFD700;
            --bg-color: #FFFDD0;
            --text-color: #333333;
            --card-bg: rgba(255, 255, 255, 0.8);
            --glass-border: rgba(255, 255, 255, 0.2);
        }

        /* Mobile-First Responsive Design */
        @media (max-width: 768px) {
            .main-title {
                font-size: 1.8rem !important;
            }
            .metric-card {
                padding: 1rem !important;
            }
            .stButton > button {
                font-size: 0.9rem !important;
                padding: 0.5rem !important;
            }
        }
        
        /* Cat mascot floating animation */
        @keyframes float {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-10px); }
        }
        
        .cat-mascot {
            animation: float 3s ease-in-out infinite;
            max-width: 80px;
            opacity: 0.9;
            transition: opacity 0.3s;
        }
        
        .cat-mascot:hover {
            opacity: 1;
            transform: scale(1.1);
        }
        
        /* Quote card styling */
        .quote-card {
            background: linear-gradient(135deg, rgba(128, 0, 32, 0.1) 0%, rgba(255, 253, 208, 0.1) 100%);
            padding: 1.5rem;
            border-left: 4px solid #800020;
            border-radius: 8px;
            margin: 1rem 0;
            font-style: italic;
            color: #800020;
            animation: slideInLeft 0.5s ease-out;
        }
        
        @keyframes slideInLeft {
            from {
                opacity: 0;
                transform: translateX(-30px);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }
        
        .quote-author {
            text-align: right;
            font-weight: 600;
            margin-top: 0.5rem;
            font-size: 0.9em;
        }
        
        /* Animated Background */
        .main-title {
            font-size: 2.5rem;
            font-weight: 700;
            background: linear-gradient(90deg, #800020 0%, #B22222 50%, #800020 100%);
            background-size: 200% auto;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            animation: gradient 3s ease infinite;
            margin-bottom: 0.5rem;
        }
        
        @keyframes gradient {
            0%, 100% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
        }
        
        .subtitle {
            color: #800020;
            font-size: 1rem;
            margin-bottom: 2rem;
            font-weight: 500;
        }
        
        /* Glassmorphism Cards */
        .metric-card {
            background: rgba(128, 0, 32, 0.05);
            backdrop-filter: blur(10px);
            padding: 1.5rem;
            border-radius: 15px;
            color: #800020;
            text-align: center;
            border: 1px solid rgba(128, 0, 32, 0.1);
            box-shadow: 0 8px 32px 0 rgba(128, 0, 32, 0.05);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        .metric-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 12px 40px 0 rgba(128, 0, 32, 0.15);
        }
        
        /* Animated Buttons */
        div.stButton > button:first-child {
            background: linear-gradient(135deg, #800020 0%, #B22222 100%);
            color: #FFFDD0;
            border: none;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
            font-weight: 600;
        }
        
        div.stButton > button:first-child:hover {
            transform: scale(1.02);
            box-shadow: 0 5px 15px rgba(128, 0, 32, 0.3);
        }
        
        div.stButton > button:first-child:active {
            transform: scale(0.98);
        }
        
        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 4px;
            background-color: transparent;
            padding: 10px 0;
        }
        
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            white-space: pre-wrap;
            background-color: rgba(255, 255, 255, 0.5);
            border-radius: 8px;
            color: #800020;
            font-weight: 600;
            transition: all 0.3s ease;
            border: 1px solid transparent;
        }
        
        .stTabs [data-baseweb="tab"]:hover {
            background-color: rgba(128, 0, 32, 0.1);
            border-color: rgba(128, 0, 32, 0.2);
        }
        
        .stTabs [aria-selected="true"] {
            background-color: #800020 !important;
            color: #FFFDD0 !important;
            box-shadow: 0 4px 10px rgba(128, 0, 32, 0.2);
        }
        
        /* Chat Message Animations */
        .stChatMessage {
            animation: slideIn 0.3s ease-out;
            background-color: rgba(255, 255, 255, 0.5);
            border-radius: 10px;
            border: 1px solid rgba(0,0,0,0.05);
        }
        
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
    </style>
    """, unsafe_allow_html=True)

def render_sidebar():
    """Render the application sidebar"""
    with st.sidebar:
        # Cat Mascot + Branding
        col_logo, col_title = st.columns([1, 3])
            st.session_state.user_api_key = st.text_input("Your Gemini API Key", type="password", value=st.session_state.get("user_api_key", ""))
            st.session_state.selected_model = "gemini-1.5-flash"
        else:
            st.info("✅ Using default API key")
            st.session_state.selected_model = "gemini-1.5-flash"
        
        st.divider()
        
        # Theme Toggle
        st.session_state.theme = st.radio("🎨 Theme", ["Light", "Dark"], horizontal=True, index=0 if st.session_state.get("theme", "Light") == "Light" else 1)
        
        st.divider()
        
        if st.button("🗑️ Clear History", use_container_width=True):
            st.session_state.prompt_history = []
            try:
                with open("history.json", "w") as f:
                    json.dump([], f)
            except:
                pass
            st.rerun()
        
        st.divider()
        st.caption("⚡ Built with Antigravity")

def render_about_page():
    """Render the About Bilota AI page"""
    st.title("📚 About Bilota AI")
    
    st.markdown("""
    <div style="background: linear-gradient(135deg, #800020 0%, #4a0012 100%); padding: 2rem; border-radius: 15px; color: white; margin-bottom: 2rem;">
        <h2 style="color: #FFD700; margin-top: 0;">Our Mission</h2>
        <p style="font-size: 1.2rem; line-height: 1.6;">
            At Bilota AI, we believe in the power of <strong>human-AI collaboration</strong>. 
            Our mission is to democratize prompt engineering, making it accessible, intuitive, and powerful for everyone.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🐱 The Bilota Story")
        st.write("""
        Bilota AI started with a simple idea: AI tools should be friendly, not intimidating. 
        Inspired by the curiosity and agility of cats (Bilota means 'Cat' in some dialects!), 
        we build tools that are agile, smart, and a little bit playful.
        """)
        
        st.info("We are a team of passionate engineers and designers dedicated to crafting the best AI experiences.")
    
    with col2:
        st.subheader("🚀 What We Do")
        st.markdown("""
        - **PromptBuddy**: Your personal AI prompt assistant.
        - **Bilota Vision**: Advanced image analysis tools.
        - **Bilota Enterprise**: Custom AI solutions for business.
        """)
        
    st.divider()
    
    if st.button("🔙 Back to App", type="primary"):
        st.session_state.show_about = False
        st.rerun()
