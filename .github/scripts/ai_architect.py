import os
import shutil
import sys
from google import genai

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

INCOMING_DIR = "incoming"
ROOT_DIR = "."

def process_scripts():
    if not os.path.exists(INCOMING_DIR):
        print("No incoming directory found. Exiting.")
        return

    for project_folder in os.listdir(INCOMING_DIR):
        project_incoming_path = os.path.join(INCOMING_DIR, project_folder)
        
        if os.path.isdir(project_incoming_path):
            final_project_path = os.path.join(ROOT_DIR, project_folder)
            if not os.path.exists(final_project_path):
                os.makedirs(final_project_path)

            for filename in os.listdir(project_incoming_path):
                filepath = os.path.join(project_incoming_path, filename)
                
                if os.path.isfile(filepath):
                    with open(filepath, "r") as f:
                        new_code = f.read()

                    print(f"🤖 AI analyzing: {filename}...")
                    
                    # --- SMART UPDATE LOGIC ---
                    target_script_path = os.path.join(final_project_path, filename)
                    is_update = os.path.exists(target_script_path)
                    
                    old_code_text = ""
                    update_instructions = "This is a brand new script."
                    
                    if is_update:
                        print("🔄 Existing script detected! Generating Release Notes...")
                        with open(target_script_path, "r") as old_f:
                            old_code = old_f.read()
                        old_code_text = f"\n\n--- OLD CODE REFERENCE ---\n{old_code}\n"
                        update_instructions = "This is an UPDATE to an existing script. Compare the OLD CODE and NEW CODE. Write the full README, but ADD a prominent '🚀 Release Notes (Latest Update)' section at the very top detailing exactly what new features or changes were added."

                    prompt = f"""
                    You are a Senior DevOps Engineer. I am adding/updating '{filename}' in my portfolio folder '{project_folder}'.
                    
                    {update_instructions}
                    
                    Analyze the NEW CODE and write a highly detailed, professional README explaining how it works, installation, and usage.
                    Output ONLY the raw Markdown text. Do not include extra conversational text.
                    
                    --- NEW CODE ---
                    {new_code}
                    {old_code_text}
                    """
                    
                    try:
                        # FIX: Using the strict '-latest' tag for the V3 SDK
                        response = client.models.generate_content(
                            model='gemini-1.5-flash-latest',
                            contents=prompt
                        )
                        
                        readme_content = response.text.strip()
                        if readme_content.startswith("```markdown"):
                            readme_content = readme_content[11:-3].strip()
                        elif readme_content.startswith("```"):
                            readme_content = readme_content[3:-3].strip()
                        
                        base_name = os.path.splitext(filename)[0]
                        md_filename = f"{base_name}.md"
                        
                        # Shutil.move automatically overwrites the old file (No duplicates!)
                        shutil.move(filepath, target_script_path)
                        
                        # Overwrite the old README with the new one containing Release Notes
                        with open(os.path.join(final_project_path, md_filename), "w") as f:
                            f.write(readme_content)
                            
                        print(f"✅ Success! Saved {filename} and {md_filename} to /{project_folder}")
                        
                    except Exception as e:
                        print(f"❌ Failed AI generation for {filename}: {e}")
                        sys.exit(1) 

            shutil.rmtree(project_incoming_path, ignore_errors=True)

if __name__ == "__main__":
    process_scripts()
