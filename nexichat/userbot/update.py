import subprocess

def install_requirements():
    try:
        subprocess.run(["pip3", "install", "--no-cache-dir", "-r", "requirements.txt"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error installing requirements: {e}")

def update():
    try:
        subprocess.run(["git", "pull", "origin", "main"], check=True)
        install_requirements()
    except subprocess.CalledProcessError as e:
        print(f"Error occurred during the update process: {e}")
