# Copyright (c) 2024 Bilota AI. All rights reserved.
# Contact: Swarit.bkp@gmail.com

"""
Core Business Logic for PromptBuddy
Handles all AI interactions, prompt generation, and analysis.
"""

import google.generativeai as genai
import streamlit as st
import json
import time
from datetime import datetime
import io
import PyPDF2
from PIL import Image
    Call Gemini API with error handling.
    
    Args:
        prompt: The user prompt
        model_name: The model to use
        system_instruction: Optional system instruction
        
    Returns:
        Generated text or error message
    """
    api_key = get_api_key()
    if not api_key:
        return "⚠️ API Key required. Enable BYOK in sidebar or check secrets."
    
    genai.configure(api_key=api_key)
    
    try:
        model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=system_instruction
        )
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error calling Gemini: {str(e)}"

def robust_call_gemini(prompt: str, model_name: str = "gemini-1.5-flash", max_retries: int = 3) -> Tuple[Optional[str], Optional[str]]:
    """
    Call Gemini with retry logic and error handling.
    
    Returns:
        Tuple (result, error_message)
    """
    for attempt in range(max_retries):
        try:
            result = call_gemini(prompt, model_name)
            if not result.startswith("Error"):
                return result, None
            # If it's a specific error we might want to retry, otherwise maybe break
            # For now, we treat "Error..." string as a failure to retry if it's transient, 
            # but call_gemini catches exceptions. Let's assume we retry on any error.
        except Exception as e:
            pass # call_gemini handles exceptions, but if we change that, this catches it.
            
        if attempt < max_retries - 1:
            time.sleep(2 ** attempt)  # Exponential backoff
    
    return None, "Max retries exceeded or API error."

def create_prompt(intent: str) -> str:
    """Generate a structured prompt from user intent"""
    meta_prompt = f"""
    You are a Prompt Engineering Expert. A user wants to achieve this:
    "{intent}"
    
    Create a high-quality, structured prompt that will help them achieve this goal.
    Use clear role definition, task specification, constraints, and output format.
    
    Output ONLY the prompt itself, nothing else.
    """
    return call_gemini(meta_prompt, "gemini-1.5-flash")

def optimize_for_model(prompt: str, target_model: str, creativity: int, specificity: int, depth: int) -> str:
    """Optimize prompt for specific model"""
    
    optimization_guides = {
        "Gemini": """
        - Use XML tags for structure (<task>, <context>, <constraints>)
        - Include system instructions separately
        - Be explicit about output format
        - Use clear hierarchical structure
        """,
        "Claude": """
        - Use Markdown structure with clear headers
        - Include chain-of-thought reasoning
        - Provide examples when possible
        - Be conversational but precise
        """,
        "GPT": """
        - Use clear, numbered instructions
        - Provide few-shot examples
        - Be explicit about format and style
        - Use role definition at start
        """,
        "Grok": """
        - Be concise and creative
        - Use humor or wit when appropriate
        - Focus on engagement and clarity
        - Avoid overly formal language
        """
    }
    
    meta_prompt = f"""
    You are optimizing a prompt for {target_model}.
    
    Original Prompt:
    {prompt}
    
    Settings:
    - Creativity: {creativity}/10
    - Specificity: {specificity}/10
    - Depth: {depth}/10
    
    Optimization Guidelines for {target_model}:
    {optimization_guides.get(target_model, "")}
    
    Rewrite this prompt to be perfectly optimized for {target_model}.
    Output ONLY the optimized prompt.
    """
    
    return call_gemini(meta_prompt, "gemini-1.5-flash")

def score_prompt(prompt: str) -> Dict[str, Any]:
    """Score a prompt on quality metrics"""
    meta_prompt = f"""
    You are a Prompt Quality Analyzer. Rate this prompt on a scale of 0-100.
    
    Prompt:
    {prompt}
    
    Evaluate on:
    1. Clarity (0-25): Is it easy to understand?
    2. Context (0-25): Does it provide enough background?
    3. Specificity (0-25): Is it precise and unambiguous?
    4. Structure (0-25): Is it well-organized?
    
    Output format (JSON):
    {{
        "total_score": 85,
        "clarity": 22,
        "context": 20,
        "specificity": 23,
        "structure": 20,
        "explanation": "Brief explanation of the score"
    }}
    
    Output ONLY valid JSON, nothing else.
    """
    
    response = call_gemini(meta_prompt, "gemini-1.5-flash")
    try:
        # Clean up potential markdown code blocks
        response = response.replace("```json", "").replace("```", "").strip()
        return json.loads(response)
    except Exception:
        return {
            "total_score": 0,
            "clarity": 0,
            "context": 0,
            "specificity": 0,
            "structure": 0,
            "explanation": "Could not parse score."
        }

def compare_prompts(prompt_a: str, prompt_b: str) -> str:
    """AI judges which prompt is better"""
    meta_prompt = f"""
    Compare these two prompts and decide which is better quality.
    
    Prompt A:
    {prompt_a}
    
    Prompt B:
    {prompt_b}
    
    Output format:
    Winner: [A/B/Tie]
    Reason: [Brief explanation]
    
    Be concise.
    """
    return call_gemini(meta_prompt, "gemini-1.5-flash")

def explain_prompt_quality(prompt: str) -> str:
    """Prompt Mentor: Explains why a prompt works or fails"""
    meta_prompt = f"""
    You are a Prompt Engineering Mentor. Analyze this prompt and explain its strengths and weaknesses.
    
    Prompt:
    {prompt}
    
    Provide analysis in this format:
    
    ✅ WHAT WORKS:
    - List 2-3 specific strengths
    
    ⚠️ WHAT NEEDS IMPROVEMENT:
    - List 2-3 specific weaknesses or gaps
    
    💡 SUGGESTIONS:
    - Provide 2-3 concrete improvement recommendations
    
    🎯 BEST USE CASES:
    - Describe 1-2 scenarios where this prompt would excel
    
    Be specific and actionable.
    """
    return call_gemini(meta_prompt, "gemini-1.5-flash")

def enhance_prompt_scoring(prompt: str) -> Dict[str, Any]:
    """Enhanced scoring with bias and readability detection"""
    meta_prompt = f"""
    You are an Advanced Prompt Quality Analyzer. Rate this prompt comprehensively.
    
    Prompt:
    {prompt}
    
    Evaluate on these dimensions (0-100 scale each):
    1. Clarity (0-20): Easy to understand?
    2. Context (0-20): Sufficient background?
    3. Specificity (0-20): Precise and unambiguous?
    4. Structure (0-20): Well-organized?
    5. Bias-Free (0-10): Free from loaded language, stereotypes, or unfair assumptions?
    6. Readability (0-10): Concise and well-written?
    
    Output format (JSON):
    {{
        "total_score": 85,
        "clarity": 18,
        "context": 17,
        "specificity": 19,
        "structure": 18,
        "bias_free": 7,
        "readability": 6,
        "explanation": "Brief overall assessment",
        "bias_notes": "Any bias concerns or 'None detected'"
    }}
    
    Output ONLY valid JSON.
    """
    response = call_gemini(meta_prompt, "gemini-1.5-flash")
    try:
        response = response.replace("```json", "").replace("```", "").strip()
        return json.loads(response)
    except Exception:
        return {
            "total_score": 0,
            "clarity": 0,
            "context": 0,
            "specificity": 0,
            "structure": 0,
            "bias_free": 0,
            "readability": 0,
            "explanation": "Could not parse score.",
            "bias_notes": "Unable to analyze"
        }

def auto_optimize_until_threshold(prompt: str, target_score: int = 90, max_iterations: int = 5) -> List[Dict[str, Any]]:
    """Evolution Engine: Iteratively optimize prompt until score >= target"""
    iterations = []
    current_prompt = prompt
    
    for i in range(max_iterations):
        # Score current prompt
        score_data = enhance_prompt_scoring(current_prompt)
        current_score = score_data.get("total_score", 0)
        
        iterations.append({
            "iteration": i + 1,
            "prompt": current_prompt,
            "score": current_score,
            "details": score_data
        })
        
        # Check if target reached
        if current_score >= target_score:
            break
        
        # If not, optimize further
        optimization_prompt = f"""
        This prompt scored {current_score}/100. Target is {target_score}.
        
        Current Prompt:
        {current_prompt}
        
        Weaknesses identified:
        - Clarity: {score_data.get('clarity', 0)}/20
        - Context: {score_data.get('context', 0)}/20
        - Specificity: {score_data.get('specificity', 0)}/20
        - Structure: {score_data.get('structure', 0)}/20
        - Bias-Free: {score_data.get('bias_free', 0)}/10
        - Readability: {score_data.get('readability', 0)}/10
        
        Rewrite this prompt to score higher. Focus on the lowest-scoring dimensions.
        Output ONLY the improved prompt, nothing else.
        """
        
        current_prompt = call_gemini(optimization_prompt, "gemini-1.5-flash")
    
    return iterations

def reflect_on_response(prompt: str, response: str) -> str:
    """Prompt Reflection: AI critiques its own response"""
    meta_prompt = f"""
    You previously received this prompt and gave a response. Now critique your own work.
    
    PROMPT:
    {prompt}
    
    YOUR RESPONSE:
    {response[:500]}...
    
    Provide honest self-reflection:
    
    🧠 REFLECTION:
    - Did you fully address the prompt?
    - What could have been better?
    - Any missed nuances or context?
    
    💡 IMPROVED PROMPT SUGGESTION:
    Suggest how the user could rephrase the prompt to get an even better response.
    
    Be brief but insightful.
    """
    return call_gemini(meta_prompt, "gemini-1.5-flash")

def analyze_image(image: Image.Image, prompt: str = "Describe this image in detail") -> str:
    """Analyze image using Gemini Vision"""
    api_key = get_api_key()
    if not api_key:
        return "⚠️ API Key required."
    
    genai.configure(api_key=api_key)
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content([prompt, image])
        return response.text
    except Exception as e:
        return f"Error analyzing image: {e}"

def generate_image(prompt: str) -> str:
    """Generate image from text (Placeholder / Fallback)"""
    return "✨ Image Generation coming in Phase 9 (Requires Imagen 3 access). For now, try Visual Studio to analyze images!"

def process_document(uploaded_file: Any) -> str:
    """Extract text from PDF or Text file"""
    try:
        if uploaded_file.type == "application/pdf":
            reader = PyPDF2.PdfReader(uploaded_file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        else:
            # Assume text file
            stringio = io.StringIO(uploaded_file.getvalue().decode("utf-8"))
            return stringio.read()
    except Exception as e:
        return f"Error processing document: {e}"

def calculate_similarity(text1: str, text2: str) -> float:
    """Simple word-overlap similarity score"""
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    return len(intersection) / len(union) if union else 0.0

def find_similar_prompts(query: str, history: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
    """Semantic Memory: Find similar prompts from history"""
    if not history:
        return []
    
    similarities = []
    for entry in history:
        prompt_text = entry.get("prompt", "")
        similarity = calculate_similarity(query, prompt_text)
        similarities.append({
            "entry": entry,
            "similarity": similarity
        })
    
    # Sort by similarity descending
    similarities.sort(key=lambda x: x["similarity"], reverse=True)
    
    return similarities[:top_k]

def process_batch_prompts(prompts_list: List[str], operation: str, **kwargs) -> List[Dict[str, Any]]:
    """Process a batch of prompts with a given operation"""
    results = []
    
    for i, prompt in enumerate(prompts_list):
        try:
            if operation == "Score":
                score_data = enhance_prompt_scoring(prompt)
                result = {
                    "prompt": prompt,
                    "status": "success",
                    "score": score_data.get("total_score", 0),
                    "details": str(score_data)
                }
            elif operation == "Optimize":
                optimized = optimize_for_model(
                    prompt, 
                    kwargs.get("target_model", "Gemini"),
                    kwargs.get("creativity", 5),
                    kwargs.get("specificity", 7),
                    kwargs.get("depth", 6)
                )
                result = {
                    "prompt": prompt,
                    "status": "success",
                    "optimized_prompt": optimized
                }
            elif operation == "Test":
                response = call_gemini(prompt, kwargs.get("model", "gemini-1.5-flash"))
                result = {
                    "prompt": prompt,
                    "status": "success",
                    "output": response
                }
            else:
                result = {"prompt": prompt, "status": "unknown operation"}
            
            results.append(result)
        except Exception as e:
            results.append({"prompt": prompt, "status": "error", "error": str(e)})
    
    return results
