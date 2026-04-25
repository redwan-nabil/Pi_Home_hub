import os
import shutil
import google.generativeai as genai

genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash-latest')

INCOMING_DIR = "incoming"

def process_scripts():
    if not os.path.exists(INCOMING_DIR):
        print("No incoming directory found. Exiting.")
        return

    for filename in os.listdir(INCOMING_DIR):
        filepath = os.path.join(INCOMING_DIR, filename)
        
        if os.path.isfile(filepath):
            with open(filepath, "r") as f:
                code = f.read()

            print(f"🤖 AI analyzing: {filename}...")
            
            prompt = f"""
            You are a Senior DevOps Engineer organizing a GitHub portfolio. 
            I have written this automation script: '{filename}'.
            
            Analyze the code and do 3 things:
            1. Assign it to a Master Category folder (e.g., 'Server_Control_Automation', 'Smart_Home_Hub', 'Network_Security'). Use underscores, no spaces.
            2. Create a documentation file name that matches the script's purpose (e.g., if the script is master_backup.sh, the doc should be 'master_backup.md').
            3. Write a highly detailed Markdown documentation file explaining the A-to-Z implementation, installation, and commands.
            
            Output STRICTLY in this exact format:
            CATEGORY: <The_Category_Name>
            MD_NAME: <The_Doc_Name.md>
            ===SPLIT===
            <The raw Markdown text>
            
            Here is the code:
            {code}
            """
            
            response = model.generate_content(prompt).text
            
            try:
                # Parse AI instructions
                parts = response.split("===SPLIT===")
                header_data = parts[0].strip().split("\n")
                readme_content = parts[1].strip()
                
                category_name = "Uncategorized_Scripts"
                md_filename = f"{filename}.md"
                
                for line in header_data:
                    if line.startswith("CATEGORY:"):
                        category_name = line.replace("CATEGORY:", "").strip()
                    elif line.startswith("MD_NAME:"):
                        md_filename = line.replace("MD_NAME:", "").strip()
                
                # Create Category Folder if it doesn't exist yet
                if not os.path.exists(category_name):
                    os.makedirs(category_name)
                
                # Move the script into the Category Folder
                new_script_path = os.path.join(category_name, filename)
                shutil.move(filepath, new_script_path)
                
                # Write the specific .md documentation file next to it
                with open(os.path.join(category_name, md_filename), "w") as f:
                    f.write(readme_content)
                    
                print(f"✅ Successfully sorted '{filename}' into '{category_name}/{md_filename}'")
                
            except Exception as e:
                print(f"❌ Failed to parse AI output for {filename}: {e}")

if __name__ == "__main__":
    process_scripts()
