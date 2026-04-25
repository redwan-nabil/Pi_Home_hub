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

    # Look at the custom folders you typed during the 'publish' command
    for project_folder in os.listdir(INCOMING_DIR):
        project_incoming_path = os.path.join(INCOMING_DIR, project_folder)
        
        if os.path.isdir(project_incoming_path):
            # Create the Master Folder in the root of your repo
            final_project_path = os.path.join(ROOT_DIR, project_folder)
            if not os.path.exists(final_project_path):
                os.makedirs(final_project_path)

            # Process the scripts inside that folder
            for filename in os.listdir(project_incoming_path):
                filepath = os.path.join(project_incoming_path, filename)
                
                if os.path.isfile(filepath):
                    with open(filepath, "r") as f:
                        code = f.read()

                    print(f"🤖 AI writing documentation for: {filename}...")
                    
                    # The prompt is now much simpler, making it crash-proof!
                    prompt = f"""
                    You are a Senior DevOps Engineer. I am adding a script named '{filename}' to my portfolio folder '{project_folder}'.
                    Analyze the code and write a highly detailed, professional README explaining how it works, installation, and usage.
                    Output ONLY the raw Markdown text. Do not include extra conversational text.
                    Code:
                    {code}
                    """
                    
                    try:
                        response = client.models.generate_content(
                            model='gemini-1.5-flash',
                            contents=prompt
                        )
                        
                        # Clean up formatting
                        readme_content = response.text.strip()
                        if readme_content.startswith("```markdown"):
                            readme_content = readme_content[11:-3].strip()
                        elif readme_content.startswith("```"):
                            readme_content = readme_content[3:-3].strip()
                        
                        # Format the MD file name (e.g. auto_backup.sh -> auto_backup.md)
                        base_name = os.path.splitext(filename)[0]
                        md_filename = f"{base_name}.md"
                        
                        # Move the code and save the new Markdown file!
                        shutil.move(filepath, os.path.join(final_project_path, filename))
                        
                        with open(os.path.join(final_project_path, md_filename), "w") as f:
                            f.write(readme_content)
                            
                        print(f"✅ Success! Saved {filename} and {md_filename} to /{project_folder}")
                        
                    except Exception as e:
                        print(f"❌ Failed AI generation for {filename}: {e}")
                        sys.exit(1) # This forces GitHub to show a Red X if the AI crashes!

            # Clean up the empty staging folder
            shutil.rmtree(project_incoming_path, ignore_errors=True)

if __name__ == "__main__":
    process_scripts()
