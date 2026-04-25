import os
import shutil
import google.generativeai as genai

# Configure AI with the secret key injected by GitHub Actions
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

INCOMING_DIR = "incoming"

def process_scripts():
    if not os.path.exists(INCOMING_DIR):
        print("No incoming directory found. Exiting.")
        return

    # Look for files pushed by the Pi
    for filename in os.listdir(INCOMING_DIR):
        filepath = os.path.join(INCOMING_DIR, filename)
        
        if os.path.isfile(filepath):
            with open(filepath, "r") as f:
                code = f.read()

            print(f"🤖 AI analyzing: {filename}...")
            
            # The prompt telling the AI exactly what to do
            prompt = f"""
            You are a Senior DevOps Engineer. I have written this automation script: '{filename}'.
            Read the code and tell me:
            1. A professional, clean Folder Name for this project (Use underscores, no spaces. e.g., Auto_Backup_System).
            2. A highly detailed, professional README.md explaining how to install and use this code.
            
            Output strictly in this format:
            FOLDER_NAME: <TheName>
            ===SPLIT===
            <The raw README.md text>
            
            Here is the code:
            {code}
            """
            
            response = model.generate_content(prompt).text
            
            try:
                # Parse the AI's response
                parts = response.split("===SPLIT===")
                folder_name = parts[0].replace("FOLDER_NAME:", "").strip()
                readme_content = parts[1].strip()
                
                # Create the new organized folder in the root directory
                if not os.path.exists(folder_name):
                    os.makedirs(folder_name)
                
                # Move the script out of 'incoming' and into its new home
                new_script_path = os.path.join(folder_name, filename)
                shutil.move(filepath, new_script_path)
                
                # Write the AI-generated README
                with open(os.path.join(folder_name, "README.md"), "w") as f:
                    f.write(readme_content)
                    
                print(f"✅ Successfully built project: {folder_name}")
                
            except Exception as e:
                print(f"❌ Failed to parse AI output for {filename}: {e}")

if __name__ == "__main__":
    process_scripts()
