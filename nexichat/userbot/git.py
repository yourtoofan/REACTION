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

    if not os.path.exists(os.path.join(repo_dir, ".git")):
        # Initialize the repository if it's not already a Git repository
        try:
            subprocess.run(["git", "init"], cwd=repo_dir, check=True)
            subprocess.run(["git", "remote", "add", "origin", repo_url], cwd=repo_dir, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error initializing Git repository: {e}")
            return

    # Pull the latest changes from the 'master' branch
    try:
        subprocess.run(["git", "fetch", "origin"], cwd=repo_dir, check=True)
        subprocess.run(["git", "pull", "origin", "master"], cwd=repo_dir, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error occurred during the update process: {e}")
        return

    # Install requirements
    try:
        subprocess.run(["pip3", "install", "--no-cache-dir", "-r", "requirements.txt"], cwd=repo_dir, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error installing requirements: {e}")
        return

    print("Update completed successfully.")
