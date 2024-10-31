import shutil
import os

def clear_cache():
    cache_dirs = [
        "cache/",
        "tmp/",
        "__pycache__"
    ]
    
    for dir in cache_dirs:
        if os.path.exists(dir):
            shutil.rmtree(dir)
            os.makedirs(dir)
