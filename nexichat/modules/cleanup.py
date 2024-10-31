from .clean_logs import clean_logs
from .clear_cache import clear_cache
from .optimize_db import optimize_database

def main():
    print("Starting cleanup process...")
    
    clean_logs()
    clear_cache()
    optimize_database()
    
    print("Cleanup completed.")
