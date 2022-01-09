import os
from datetime import datetime, timedelta

def file_list(directory, ext = ".csv", startswith = ""):
    return [
            directory + f for f in os.listdir(directory) 
            if os.path.isfile(os.path.join(directory, f)) 
            and f.startswith(startswith)
            and f.endswith(ext)
            ]
            
