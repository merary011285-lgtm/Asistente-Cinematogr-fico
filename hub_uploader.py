import os
import subprocess
import sys

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
    print("🎬 Cinematographic Assistant: HUB Uploader (APY)")
    print("===============================================")
    
    # 1. Check for Git
    git_check = run_command("git --version")
    if not git_check:
        print("❌ Git not found. Please install Git to use this uploader.")
        return

    # 2. Initialize Repo if not exists
    if not os.path.exists(".git"):
        print("📦 Initializing local repository...")
        run_command("git init")
        run_command("git branch -M main")
    
    # 3. Add Files
    print("➕ Adding files to staging...")
    run_command("git add cinematography_assistant.py prompt_templates.json requirements.txt .agent/skills")
    
    # 4. Commit
    commit_msg = input("📝 Enter commit message (default: 'Update assistant from laptop'): ") or "Update assistant from laptop"
    run_command(f'git commit -m "{commit_msg}"')
    
    # 5. Push (Requires Remote Setup)
    remote_check = run_command("git remote -v")
    if not remote_check:
        print("\n⚠️ No remote repository configured!")
        repo_url = input("🔗 Please enter your GitHub Repository URL: ")
        if repo_url:
            run_command(f"git remote add origin {repo_url}")
            print(f"✅ Remote 'origin' added: {repo_url}")
        else:
            print("❌ Push cancelled. Configure remote manually with 'git remote add origin <url>'.")
            return

    print("\n🚀 Pushing to Cloud Hub...")
    push_result = run_command("git push -u origin main")
    
    if push_result is not None:
        print("\n✨ SUCCESS: Your assistant is now synced with the Hub!")
        print("💡 The Cloud Hub should auto-redeploy in a few seconds.")
    else:
        print("\n❌ FAILED to push. Check your internet connection or GitHub permissions.")

if __name__ == "__main__":
    main()
