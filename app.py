# Copyright (c) 2024 Bilota AI. All rights reserved.
# Contact: Swarit.bkp@gmail.com

"""
PromptBuddy - By Bilota AI
Main entry point for the application.
"""

import streamlit as st
import ui_components
import tools_ui
import utils
import logic
import json
import os

# Force Reload Trigger: 1
# --- Page Config ---
st.set_page_config(
    page_title="Gemini 3 Architect - By Bilota AI",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Initialization ---

# Initialize Session State
if "use_own_key" not in st.session_state:
    st.session_state.use_own_key = False
if "user_api_key" not in st.session_state:
    st.session_state.user_api_key = ""
if "prompt_history" not in st.session_state:
    st.session_state.prompt_history = []
if "theme" not in st.session_state:
    st.session_state.theme = "Light"
if "selected_model" not in st.session_state:
    st.session_state.selected_model = "gemini-1.5-flash"
if "onboarding_complete" not in st.session_state:
    st.session_state.onboarding_complete = False
if "version_history" not in st.session_state:
    st.session_state.version_history = {}
if "show_mobile_warning" not in st.session_state:
    st.session_state.show_mobile_warning = True
if "show_about" not in st.session_state:
    st.session_state.show_about = False
if "templates" not in st.session_state:
    templates, error = utils.load_templates()
    if templates:
        st.session_state.templates = templates
    else:
        st.session_state.templates = {}
if "current_project" not in st.session_state:
    st.session_state.current_project = {"id": "default", "name": "Default Project"}

# Load History
if not st.session_state.prompt_history:
    # 1. Try Cloud History if logged in
    if "user" in st.session_state and st.session_state.user and not st.session_state.user.get("local"):
        try:
            history, msg = utils.load_history_from_firestore(st.session_state.user["uid"])
            if history:
                st.session_state.prompt_history = history
                # st.toast(f"☁️ {msg}") # Optional: Notify user
        except Exception as e:
            print(f"Error loading cloud history: {e}")

    # 2. Fallback to Local History if still empty
    if not st.session_state.prompt_history:
        try:
            if os.path.exists("history.json"):
                with open("history.json", "r") as f:
                    st.session_state.prompt_history = json.load(f)
        except:
            pass

# --- Render UI ---

# 1. Custom CSS
ui_components.render_custom_css()

# 2. Sidebar
ui_components.render_sidebar()

# 3. Main Content
if st.session_state.show_about:
    ui_components.render_about_page()
else:
    # Render the main tools interface
    tools_ui.render_tools_page()
