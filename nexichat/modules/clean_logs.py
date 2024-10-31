import os
import time

def clean_logs():
    log_dir = "logs/"
    current_time = time.time()
    days_to_keep = 7
    
    for filename in os.listdir(log_dir):
        filepath = os.path.join(log_dir, filename)
        if os.path.getmtime(filepath) < (current_time - (days_to_keep * 86400)):
            os.remove(filepath)
