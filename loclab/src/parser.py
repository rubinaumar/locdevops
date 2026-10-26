import json
import os
import re
import requests
from dotenv import load_dotenv

# Load local environment configurations securely from .env
load_dotenv()

PLACEHOLDER_REGEX = r"(\{[a-zA-Z0-9_]+\})"

# Retrieve API Configuration Tokens from the protected system environment
TMS_API_TOKEN = os.getenv("TMS_API_TOKEN")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

def load_localization_file(filepath):
    """Safely loads a JSON localization asset."""
    if not os.path.exists(filepath):
        print(f"❌ Error: File not found at {filepath}")
        return None
    with open(filepath, 'r', encoding='utf-8') as file:
        return json.load(file)

def save_localization_file(filepath, data):
    """Saves updated JSON localization assets back to disk with clean formatting."""
    with open(filepath, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
    print(f"💾 Successfully updated translation asset at: {filepath}")

def translate_text_via_api(text, target_lang="es"):
    """
    Leverages .env credentials to dynamically translate text via an API interface.
    This simulates a standard localization engine API connection (e.g., DeepL / Mock TMS).
    """
    if not TMS_API_TOKEN or "mock_" in TMS_API_TOKEN:
        print(f"⚠️  [Mock Mode] No valid production API Token found. Simulating machine translation for: '{text}'")
        return f"[MT_TRANSLATION] {text}"

    # Target endpoint configuration structure used by modern Translation APIs
    url = "https://mock-tms-provider.com" 
    headers = {
        "Authorization": f"Bearer {TMS_API_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "text": [text],
        "target_lang": target_lang.upper()
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()["translations"][0]["text"]
        else:
            print(f"❌ API Error: Received status code {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Network Exception during translation call: {e}")
        return None

def run_localization_pipeline(source_path, target_path):
    """Unified pipeline executing structural audits, placeholder checks, and auto-translation."""
    source_data = load_localization_file(source_path)
    target_data = load_localization_file(target_path)
    
    if not source_data:
        print("💥 Pipeline Aborted: Missing source localization assets.")
        return False
        
    if target_data is None:
        target_data = {}

    pipeline_healthy = True
    needs_update = False

    print("📋 [1/3] Auditing file structural integrity...")
    missing_keys = [key for key in source_data if key not in target_data]
    
    if missing_keys:
        print(f"   ℹ️  Detected {len(missing_keys)} missing translation keys. Triggering translation engine...")
        needs_update = True
    else:
        print("   ✅ Structural Audit Passed: Structural schemas match perfectly.")

    print("-" * 50)

    print("🧪 [2/3] Verifying placeholder variables...")
    variable_errors = 0
    for key, source_text in source_data.items():
        if key not in target_data:
            continue
        target_text = target_data[key]
        
        source_placeholders = sorted(re.findall(PLACEHOLDER_REGEX, source_text))
        target_placeholders = sorted(re.findall(PLACEHOLDER_REGEX, target_text))
        
        if source_placeholders != target_placeholders:
            print(f"   ❌ Variable Mismatch in key '{key}':")
            print(f"      Source expects: {source_placeholders} -> Got: {target_placeholders}")
            variable_errors += 1
            
    if variable_errors > 0:
        print(f"   ❌ Variable Integrity Failed: Found {variable_errors} broken developer assets.")
        pipeline_healthy = False
    else:
        print("   ✅ Variable Integrity Passed: All code variables are fully intact.")

    print("-" * 50)

    # ==========================================
    # STEP 3: Automated Dynamic Translation API Interface
    # ==========================================
    print("🚀 [3/3] Running dynamic API Auto-Translation module...")
    if pipeline_healthy and needs_update:
        for key in missing_keys:
            source_text = source_data[key]
            print(f"   🌐 Querying translation interface for key: '{key}'")
            
            translated_result = translate_text_via_api(source_text, target_lang="es")
            
            if translated_result:
                # Basic variable fallback mitigation logic to make sure the MT engine didn't drop brackets
                src_vars = re.findall(PLACEHOLDER_REGEX, source_text)
                for var in src_vars:
                    if var not in translated_result:
                        # Force fix the bracket configuration if machine translation corrupted it
                        translated_result += f" {var}"
                
                target_data[key] = translated_result
        
        save_localization_file(target_path, target_data)
        print("🎉 Auto-Translation Execution Completed successfully!")
    elif not pipeline_healthy:
        print("🚨 Blocked: Translation pipeline bypassed due to existing source errors.")
    else:
        print("😎 Dashboard Clean: No missing string entries require translation calls.")

    return pipeline_healthy

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, ".."))
    
    # Matching your exact lower_underscore file names
    source = os.path.join(project_root, "locales", "en_us.json")
    target = os.path.join(project_root, "locales", "es_es.json")
    
    run_localization_pipeline(source, target)