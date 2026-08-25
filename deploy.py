# -*- coding: utf-8 -*-
import os
import sys
import subprocess
import datetime

# Ensure stdout uses UTF-8 on Windows
if sys.platform == 'win32':
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
        os.system('color 0A')
    except Exception:
        pass

def run_cmd(command, check=False):
    """Run a shell command and return exit code and output."""
    result = subprocess.run(command, shell=True, text=True, capture_output=True, encoding='utf-8', errors='replace')
    if check and result.returncode != 0:
        print(f"[Error]: {result.stderr.strip()}")
    return result.returncode, result.stdout.strip(), result.stderr.strip()

def main():
    print("=" * 79)
    print("  🚀 កម្មវិធីស្វ័យប្រវត្តិ៖ រុញកូដទៅ GitHub និង Deploy ទៅកាន់ Vercel")
    print("  ☕ Boba POS System - Auto Deploy Tool")
    print("=" * 79)
    print()

    # 1. ពិនិត្យមើល Git
    code, _, _ = run_cmd("git --version")
    if code != 0:
        print("❌ [កំហុស] រកមិនឃើញកម្មវិធី Git ក្នុងកុំព្យូទ័រនេះទេ!")
        print("   សូមដំឡើង Git ជាមុនសិន: https://git-scm.com/")
        input("\nចុច Enter ដើម្បីចាកចេញ...")
        return

    # 2. ពិនិត្យមើល Git Repository
    if not os.path.exists(".git"):
        print("[*] កំពុងបង្កើត Git Repository ថ្មី...")
        run_cmd("git init -b main")
        print()

    # 3. ពិនិត្យមើល Remote Origin
    code, remote_url, _ = run_cmd("git remote get-url origin")
    if code != 0 or not remote_url:
        print("⚠️ [!] មិនទាន់មាន Link GitHub Repository នៅឡើយទេ។")
        repo_url = input("👉 សូមបញ្ចូល Link GitHub Repo របស់អ្នក (ឧ. https://github.com/username/pos.git): ").strip()
        if not repo_url:
            print("❌ [កំហុស] អ្នកមិនបានបញ្ចូល Link GitHub ទេ!")
            input("\nចុច Enter ដើម្បីចាកចេញ...")
            return
        run_cmd(f"git remote add origin {repo_url}")
        print(f"✅ បានភ្ជាប់ទៅកាន់: {repo_url}\n")

    # 4. សួររក Commit Message
    print("-" * 79)
    print("[*] កំពុងរៀបចំ File ទាំងអស់ដើម្បី Push...")
    print()
    user_msg = input("📝 សូមវាយអត្ថន័យនៃការ Update (ឬចុច Enter យកលំនាំដើម): ").strip()
    
    if not user_msg:
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        user_msg = f"Update POS Tea - {now_str}"

    print(f"\n[*] កំពុង Add Files (git add .)...")
    run_cmd("git add .")

    print(f"[*] កំពុងបង្កើត Commit: '{user_msg}'...")
    run_cmd(f'git commit -m "{user_msg}"')

    print("[*] កំពុងរុញកូដឡើងទៅកាន់ GitHub (git push origin main)...")
    run_cmd("git branch -M main")
    
    # Run git push with direct output to show progress/credential prompts
    push_process = subprocess.run("git push -u origin main", shell=True)

    if push_process.returncode == 0:
        print()
        print("=" * 79)
        print("  🎉 ជោគជ័យ! (DEPLOYMENT SUCCESS)")
        print("  " + "-" * 73)
        print("  ✅ កូដត្រូវបាន Push ទៅកាន់ GitHub រួចរាល់ដោយជោគជ័យ!")
        print("  🚀 Vercel នឹងចាប់ផ្ដើម Deploy ដោយស្វ័យប្រវត្តិក្នុងរយៈពេលប្រហែល ១ នាទី។")
        print()
        print("  🌐 ពិនិត្យមើលវេបសាយផ្ទាល់: https://pos-six-murex.vercel.app")
        print("  📊 ពិនិត្យមើល Vercel Dashboard: https://vercel.com/")
        print("=" * 79)
    else:
        print()
        print("=" * 79)
        print("  ⚠️ ការ Push មិនទាន់បានសម្រេច! (PUSH FAILED)")
        print("  " + "-" * 73)
        print("  សូមពិនិត្យមើល៖")
        print("  1. ត្រូវប្រាកដថាបាន Login GitHub ក្នុងម៉ាស៊ីនរួចរាល់")
        print("  2. ពិនិត្យមើល Link GitHub Repository ថាត្រឹមត្រូវដែរឬទេ")
        print("=" * 79)

    print()
    input("ចុច Enter ដើម្បីបិទផ្ទាំងនេះ...")

if __name__ == '__main__':
    main()
