# TSS Logging

import datetime
from datetime import timezone 

def tsslogit(message):
  repo=""    
  now = datetime.datetime.now(timezone.utc)
  dbuf = "[INFO " + now.strftime("%Y-%m-%d_%H:%M:%S") + "]"
  
  with open("/tmux/reponame.txt", "r") as file1:
    # Reading from a file
    repo=file1.read()

    #[INFO 2024-08-18_19:24:06]
  with open("/{}/tml-airflow/logs/logs.txt".format(repo), "a") as file1:
    # Reading from a file
    dbuf = "[INFO " + now.strftime("%Y-%m-%d_%H:%M:%S") + "]"
    file1.write("{} {}\n".format(dbuf,message))
