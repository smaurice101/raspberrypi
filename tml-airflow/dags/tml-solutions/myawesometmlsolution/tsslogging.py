# TSS Logging

import datetime
from datetime import timezone 
from git import Repo
import socketserver

def tmuxchange(tmuxname):
  with open("/tmux/tmux-airflow.sh", "a") as myfile:
    myfile.write("airflow dags trigger {}".format(tmuxname))
    
def getfreeport():
  with socketserver.TCPServer(("localhost", 0), None) as s:
    free_port = s.server_address
  return free_port[1]

def getrepo(filename='/tmux/reponame.txt'):
  with open(filename, "r") as file1:
    # Reading from a file
    repo=file1.read()
    repo=repo.rstrip()
    
  return repo

def git_push(repopath,message,sname):
    try:
        repo = Repo(repopath)
        repo.git.add(update=True)
        repo.index.commit(message)
        origin = repo.remote(name=sname)
        origin.push()
    except:
        print('Some error occured while pushing the code')    

def tsslogit(message,mtype="INFO"):
  repo=""    
  now = datetime.datetime.now(timezone.utc)
  dbuf = "[INFO " + now.strftime("%Y-%m-%d_%H:%M:%S") + "]"
  
  repo=getrepo()  

    #[INFO 2024-08-18_19:24:06]
  with open("/{}/tml-airflow/logs/logs.txt".format(repo), "a") as file1:
    # Reading from a file
    dbuf = "[{} {}]".format(mtype,now.strftime("%Y-%m-%d_%H:%M:%S"))
    file1.write("{} {}\n".format(dbuf,message))
