import subprocess
import os

def run_command(command):
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error executing: {command}")
        print(f"Output: {e.output}")
        print(f"Error: {e.stderr}")
        return None

def main():
    print("Cinematographic Assistant: HUB Uploader (APY)")
    print("===============================================")
    
    # 1. Check for Git
    git_version = run_command("git --version")
    if not git_version:
        print("Git not found. Please install Git to use this uploader.")
        return

    # 2. Initialize Repo if not exists
    if not os.path.exists(".git"):
        print("Initializing local repository...")
        run_command("git init")
        run_command("git branch -M main")
    
    # 3. Add Files
    print("Adding files to staging...")
    run_command("git add cinematography_assistant.py prompt_templates.json requirements.txt README.md .gitignore secrets_template.toml")
    
    # 4. Commit
    commit_msg = input("Enter commit message (default: 'Update Assistant V2.7'): ") or "Update Assistant V2.7"
    run_command(f'git commit -m "{commit_msg}"')
    
    # 5. Remote Check
    remote_exists = run_command("git remote -v")
    if not remote_exists:
        repo_url = input("Enter GitHub Repository URL: ")
        if repo_url:
            run_command(f"git remote add origin {repo_url}")
            run_command("git push -u origin main")
    else:
        print("Starting synchronization...")
        run_command("git push")
        print("Synchronization completed successfully!")

if __name__ == "__main__":
    main()
