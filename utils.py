"""
Utility functions for PromptBuddy
Handles export/import, versioning, metrics, and helpers
"""

import json
import csv
import io
import uuid
import os
import time
from datetime import datetime
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple, Union

# --- Export/Import Functions ---

def export_to_json(data: List[Dict[str, Any]], filename: str = "prompts_export.json") -> Tuple[Optional[str], Optional[str]]:
    """Export prompts to JSON format"""
    try:
        json_str = json.dumps(data, indent=2)
        return json_str, filename
    except Exception as e:
        return None, f"Error: {e}"

def export_to_csv(data: List[Dict[str, Any]], filename: str = "prompts_export.csv") -> Tuple[Optional[str], Optional[str]]:
    """Export prompts to CSV format"""
    try:
        if not data:
            return None, "No data to export"
        
        output = io.StringIO()
        # Ensure we handle potential missing keys by getting all unique keys
        keys = set().union(*(d.keys() for d in data))
        writer = csv.DictWriter(output, fieldnames=list(keys))
        writer.writeheader()
        writer.writerows(data)
        
        return output.getvalue(), filename
    except Exception as e:
        return None, f"Error: {e}"

def export_to_markdown(data: List[Dict[str, Any]], filename: str = "prompts_export.md") -> Tuple[Optional[str], Optional[str]]:
    """Export prompts to Markdown format"""
    try:
        md_content = "# PromptBuddy Export\n\n"
        md_content += f"**Exported:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        md_content += f"**Total Prompts:** {len(data)}\n\n---\n\n"
        
        for i, entry in enumerate(data, 1):
            md_content += f"## {i}. {entry.get('prompt', 'Untitled')[:50]}...\n\n"
            md_content += f"**Model:** {entry.get('model', 'N/A')}\n\n"
            md_content += f"**Score:** {entry.get('score', 0)}/100\n\n"
            md_content += f"**Timestamp:** {entry.get('timestamp', 'N/A')}\n\n"
            md_content += f"```\n{entry.get('prompt', '')}\n```\n\n"
            if entry.get('output'):
                md_content += f"**Output:**\n\n{entry.get('output', '')}\n\n"
            md_content += "---\n\n"
        
        return md_content, filename
    except Exception as e:
        return None, f"Error: {e}"

def import_from_json(file_content: str) -> Tuple[Optional[List[Dict[str, Any]]], str]:
    """Import prompts from JSON"""
    try:
        data = json.loads(file_content)
        if isinstance(data, list):
            return data, f"Imported {len(data)} prompts"
        else:
            return [data], "Imported 1 prompt"
    except Exception as e:
        return None, f"Error parsing JSON: {e}"

def import_from_csv(file_content: str) -> Tuple[Optional[List[Dict[str, Any]]], str]:
    """Import prompts from CSV"""
    try:
        stringio = io.StringIO(file_content)
        reader = csv.DictReader(stringio)
        data = list(reader)
        return data, f"Imported {len(data)} prompts"
    except Exception as e:
        return None, f"Error parsing CSV: {e}"

# --- Version Control Functions ---

def create_version(prompt: str, score: int = 0, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Create a new version entry"""
    return {
        "id": str(uuid.uuid4()),
        "content": prompt,
        "score": score,
        "timestamp": datetime.now().isoformat(),
        "metadata": metadata or {}
    }

def add_version_to_history(prompt_id: str, version: Dict[str, Any], version_history: Dict[str, Any]) -> Dict[str, Any]:
    """Add a version to the version history"""
    if prompt_id not in version_history:
        version_history[prompt_id] = {
            "prompt_id": prompt_id,
            "versions": []
        }
    
    version_history[prompt_id]["versions"].append(version)
    return version_history

def get_versions(prompt_id: str, version_history: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get all versions for a prompt"""
    return version_history.get(prompt_id, {}).get("versions", [])

def compare_versions(version1: Dict[str, Any], version2: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a diff between two versions"""
    import difflib
    
    d = difflib.Differ()
    diff = list(d.compare(version1["content"].splitlines(), version2["content"].splitlines()))
    
    return {
        "version1_score": version1.get("score", 0),
        "version2_score": version2.get("score", 0),
        "score_delta": version2.get("score", 0) - version1.get("score", 0),
        "diff": "\n".join(diff),
        "timestamp1": version1.get("timestamp"),
        "timestamp2": version2.get("timestamp")
    }

# --- Prompt Metrics Functions ---

def calculate_prompt_metrics(prompt: str) -> Dict[str, Any]:
    """Calculate various metrics for a prompt"""
    if not prompt:
        return {
            "word_count": 0,
            "char_count": 0,
            "line_count": 0,
            "avg_word_length": 0,
            "sentence_count": 0,
            "reading_time_seconds": 0,
            "complexity_score": 0
        }
        
    metrics = {
        "word_count": len(prompt.split()),
        "char_count": len(prompt),
        "line_count": len(prompt.splitlines()),
        "avg_word_length": sum(len(word) for word in prompt.split()) / max(len(prompt.split()), 1),
        "sentence_count": prompt.count('.') + prompt.count('!') + prompt.count('?'),
    }
    
    # Estimate reading time (avg 200 words/min)
    metrics["reading_time_seconds"] = int((metrics["word_count"] / 200) * 60)
    
    # Simple complexity score (0-100)
    # Based on length, vocabulary, and structure
    complexity = min(100, (
        (metrics["word_count"] / 5) +  # Longer = more complex
        (metrics["avg_word_length"] * 5) +  # Bigger words = more complex
        (metrics["sentence_count"] * 2)  # More sentences = more complex
    ))
    metrics["complexity_score"] = int(complexity)
    
    return metrics

def estimate_token_cost(prompt: str, model: str = "gemini-1.5-flash") -> Dict[str, Any]:
    """Estimate API cost for a prompt"""
    # Very rough estimation: ~1.3 tokens per word for English
    estimated_tokens = int(len(prompt.split()) * 1.3)
    
    # Pricing (these are example rates, update with actual)
    pricing = {
        "gemini-1.5-pro": {"input": 0.0000035, "output": 0.0000105},  # per 1 token (approx)
        "gemini-1.5-flash": {"input": 0.000000075, "output": 0.0000003},
    }
    
    rate = pricing.get(model, pricing["gemini-1.5-flash"])
    
    # Assume average response is 2x the prompt length
    input_cost = estimated_tokens * rate["input"]
    output_cost = (estimated_tokens * 2) * rate["output"]
    total_cost = input_cost + output_cost
    
    return {
        "estimated_tokens": estimated_tokens,
        "input_cost_usd": round(input_cost, 8),
        "output_cost_usd": round(output_cost, 8),
        "total_cost_usd": round(total_cost, 8),
        "cost_formatted": f"${total_cost:.8f}"
    }

def calculate_readability(text: str) -> Dict[str, Any]:
    """Calculate Flesch Reading Ease score"""
    try:
        import textstat
        score = textstat.flesch_reading_ease(text)
        
        # Interpret score
        if score >= 90:
            level = "Very Easy (5th grade)"
        elif score >= 80:
            level = "Easy (6th grade)"
        elif score >= 70:
            level = "Fairly Easy (7th grade)"
        elif score >= 60:
            level = "Standard (8th-9th grade)"
        elif score >= 50:
            level = "Fairly Difficult (10th-12th grade)"
        elif score >= 30:
            level = "Difficult (College)"
        else:
            level = "Very Difficult (College Graduate)"
        
        return {"score": round(score, 1), "level": level}
    except ImportError:
        # Fallback if textstat not available
        return {"score": 0, "level": "Install textstat for readability analysis"}
    except Exception:
        return {"score": 0, "level": "Error calculating readability"}

# --- Template Functions ---

def load_templates(filepath: str = "templates.json") -> Tuple[Optional[Dict[str, List[Dict[str, Any]]]], Optional[str]]:
    """Load prompt templates from JSON file"""
    try:
        if not os.path.exists(filepath):
            return None, "Templates file not found"
            
        with open(filepath, 'r', encoding='utf-8') as f:
            templates = json.load(f)
        return templates, None
    except Exception as e:
        return None, f"Error loading templates: {e}"

def search_templates(templates: Dict[str, List[Dict[str, Any]]], query: str) -> List[Dict[str, Any]]:
    """Search templates by name, tags, or content"""
    results = []
    query = query.lower()
    
    for category, category_templates in templates.items():
        for template in category_templates:
            # Search in name, prompt, and tags
            searchable = f"{template['name']} {template['prompt']} {' '.join(template.get('tags', []))}".lower()
            if query in searchable:
                results.append({
                    **template,
                    "category": category
                })
    
    return results

# --- Analytics Functions ---

def calculate_trends(history_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate trends from history data"""
    if not history_data or len(history_data) < 2:
        return {
            "total_prompts": len(history_data) if history_data else 0,
            "avg_score": 0,
            "score_trend": "stable",
            "most_used_model": "N/A",
            "prompts_this_week": 0
        }
    
    # Convert to DataFrame for easier analysis
    df = pd.DataFrame(history_data)
    
    # Calculate trend indicators
    trends = {
        "total_prompts": len(df),
        "avg_score": df["score"].mean() if "score" in df else 0,
        "score_trend": "improving" if len(df) > 10 and df.tail(5)["score"].mean() > df.head(5)["score"].mean() else "stable",
        "most_used_model": df["model"].mode()[0] if "model" in df and len(df["model"].mode()) > 0 else "N/A",
        "prompts_this_week": len(df[pd.to_datetime(df["timestamp"]) > (datetime.now() - pd.Timedelta(days=7))]) if "timestamp" in df else 0
    }
    
    return trends

# --- Firestore Sync Functions ---

def sync_history_to_firestore(history: List[Dict[str, Any]], user_id: str) -> Tuple[bool, str]:
    """Sync local history to Firestore"""
    import firebase_config
    db, _, status, _ = firebase_config.initialize_firebase()
    
    if status != "connected" or not db:
        return False, "Not connected to Firestore"
        
    try:
        # Overwrite user's history document
        # Structure: users/{uid}/history/prompt_history
        doc_ref = db.collection("users").document(user_id).collection("history").document("prompt_history")
        doc_ref.set({"entries": history})
        return True, "Synced to cloud"
    except Exception as e:
        return False, f"Sync failed: {e}"

def load_history_from_firestore(user_id: str) -> Tuple[List[Dict[str, Any]], str]:
    """Load history from Firestore"""
    import firebase_config
    db, _, status, _ = firebase_config.initialize_firebase()
    
    if status != "connected" or not db:
        return [], "Not connected"
        
    try:
        doc_ref = db.collection("users").document(user_id).collection("history").document("prompt_history")
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict().get("entries", []), "Loaded from cloud"
        else:
            return [], "No cloud history found"
    except Exception as e:
        return [], f"Load failed: {e}"

# --- Project & Chat Management (Phase 6) ---

def get_projects(user_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get list of projects (Local or Cloud)"""
    # Cloud
    if user_id:
        import firebase_config
        db, _, status, _ = firebase_config.initialize_firebase()
        if status == "connected" and db:
            try:
                docs = db.collection("users").document(user_id).collection("projects").stream()
                return [{"id": d.id, **d.to_dict()} for d in docs]
            except:
                pass
    
    # Local Fallback
    try:
        if os.path.exists("projects.json"):
            with open("projects.json", "r") as f:
                return json.load(f)
    except:
        pass
    return [{"id": "default", "name": "Default Project", "created_at": str(datetime.now())}]

def create_project(user_id: Optional[str], project_name: str) -> bool:
    """Create a new project"""
    project_id = str(uuid.uuid4())
    new_project = {
        "id": project_id,
        "name": project_name,
        "created_at": str(datetime.now()),
        "created_by": user_id or "local"
    }
    
    # Cloud
    if user_id:
        import firebase_config
        db, _, status, _ = firebase_config.initialize_firebase()
        if status == "connected" and db:
            try:
                db.collection("users").document(user_id).collection("projects").document(project_id).set(new_project)
                return True
            except Exception as e:
                print(f"Error creating cloud project: {e}")
                return False
    
    # Local
    try:
        projects = get_projects()
        projects.append(new_project)
        with open("projects.json", "w") as f:
            json.dump(projects, f)
        return True
    except Exception as e:
        print(f"Error creating local project: {e}")
        return False

def listen_to_history(user_id: str, project_id: str = "default"):
    """
    Setup real-time listener for history.
    Note: Streamlit doesn't support persistent background listeners well.
    This is a helper to fetch latest data, simulating 'sync'.
    """
    import firebase_config
    db, _, status, _ = firebase_config.initialize_firebase()
    
    if status != "connected" or not db:
        return None
        
    try:
        # In a real app, we'd use on_snapshot, but for Streamlit we just fetch
        # filtering by project_id would happen here
        doc_ref = db.collection("users").document(user_id).collection("history").document("prompt_history")
        doc = doc_ref.get()
        if doc.exists:
            data = doc.to_dict().get("entries", [])
            # Filter by project if we had that field in entries, for now return all
            return data
    except:
        return None

# --- File Storage (Phase 7) ---

def upload_file(file_obj, user_id: str, folder: str = "uploads") -> Optional[str]:
    """Upload a file to Firebase Storage and return public URL"""
    import firebase_config
    _, _, status, _ = firebase_config.initialize_firebase()
    
    if status != "connected":
        return None
        
    try:
        bucket = firebase_config._app.storage().bucket() if hasattr(firebase_config._app, 'storage') else None
        # Fallback if storage not directly accessible via app
        if not bucket:
             # Try to get bucket from config if possible, or assume default
             from firebase_admin import storage
             bucket = storage.bucket()

        blob_name = f"users/{user_id}/{folder}/{str(uuid.uuid4())}_{file_obj.name}"
        blob = bucket.blob(blob_name)
        
        blob.upload_from_file(file_obj, content_type=file_obj.type)
        blob.make_public()
        
        return blob.public_url
    except Exception as e:
        print(f"Upload failed: {e}")
        return None

def list_user_files(user_id: str, folder: str = "uploads") -> List[Dict[str, Any]]:
    """List user's uploaded files"""
    import firebase_config
    _, _, status, _ = firebase_config.initialize_firebase()
    
    if status != "connected":
        return []
        
    try:
        from firebase_admin import storage
        bucket = storage.bucket()
        prefix = f"users/{user_id}/{folder}/"
        blobs = bucket.list_blobs(prefix=prefix)
        
        files = []
        for blob in blobs:
            files.append({
                "name": blob.name.split('/')[-1],
                "url": blob.public_url,
                "content_type": blob.content_type,
                "size": blob.size,
                "updated": blob.updated
            })
        return files
    except Exception as e:
        print(f"List files failed: {e}")
        return []

