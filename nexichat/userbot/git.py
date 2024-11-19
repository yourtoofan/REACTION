import os
import subprocess
import config

def update(repo_dir="/app"):
    """
    Pull the latest changes from the Git repository and install requirements.
    :param repo_dir: Path to the directory where the Git repository is located.
    """
    repo_url = config.UPSTREAM_REPO

    if not repo_url:
        print("Error: UPSTREAM_REPO is not defined in the configuration.")
        return

    # Check if the directory is a valid Git repository
    if not os.path.exists(os.path.join(repo_dir, ".git")):
        try:
            print("Initializing Git repository...")
            subprocess.run(["git", "init"], cwd=repo_dir, check=True)
            subprocess.run(["git", "remote", "add", "origin", repo_url], cwd=repo_dir, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error initializing Git repository: {e}")
            return

    # Pull the latest changes
    try:
        print("Fetching latest changes from the repository...")
        subprocess.run(["git", "fetch", "origin"], cwd=repo_dir, check=True)
        subprocess.run(["git", "reset", "--hard", "origin/main"], cwd=repo_dir, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error occurred during the update process: {e}")
        return

    # Install requirements
    requirements_file = os.path.join(repo_dir, "requirements.txt")
    if os.path.exists(requirements_file):
        try:
            print("Installing dependencies from requirements.txt...")
            subprocess.run(["pip3", "install", "--no-cache-dir", "-r", requirements_file], cwd=repo_dir, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error installing requirements: {e}")
            return
    else:
        print("No requirements.txt found. Skipping dependency installation.")

    print("Update completed successfully.")
