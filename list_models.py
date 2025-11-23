# Copyright (c) 2024 Bilota AI. All rights reserved.
# Contact: Swarit.bkp@gmail.com

import google.generativeai as genai
import streamlit as st
import os

# Try to get key from secrets or environment
try:
    import toml
    secrets = toml.load(".streamlit/secrets.toml")
    api_key = secrets["GEMINI_API_KEY"]
except:
    print("Could not load secrets.toml")
    api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("No API key found.")
else:
    genai.configure(api_key=api_key)
    print("Listing available models:")
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"- {m.name}")
    except Exception as e:
        print(f"Error listing models: {e}")
