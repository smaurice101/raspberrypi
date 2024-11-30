# TSS Logging

# TSS Logging

import datetime
from datetime import timezone 
from git import Repo
import socketserver
import subprocess
import os
import socket
import time

def genkubeyaml(sname,containername,clientport,solutionairflowport,solutionvipervizport,solutionexternalport,sdag,guser,grepo,chip,dockerusername,externalport,kuser,mqttuser,airflowport,vipervizport):
    cp = ""
    cpp = ""
    if len(clientport) > 1:
        cp = """    - containerPort: {}
            - containerPort: {}
            - containerPort: {}
            - containerPort: {}""".format(clientport,solutionairflowport,solutionvipervizport,solutionexternalport)
        cpp = clientport
        cs="""  - port: {}
         name: p1
         protocol: TCP
         targetPort: {}
       - port: {}
         name: p2
         protocol: TCP
         targetPort: {}
       - port: {}
         name: p3
         protocol: TCP
         targetPort: {}
       - port: {}
         name: p4
         protocol: TCP
         targetPort: {}""".format(clientport,clientport,solutionairflowport,solutionairflowport,solutionvipervizport,solutionvipervizport,solutionexternalport,solutionexternalport)
        
    else:    
        cp = """   - containerPort: {}
            - containerPort: {}
            - containerPort: {}""".format(solutionexternalport,solutionairflowport,solutionvipervizport)
        cpp = "0"
        cs="""  - port: {}
         name: p2
         protocol: TCP
         targetPort: {}
       - port: {}
         name: p3
         protocol: TCP
         targetPort: {}
       - port: {}
         name: p4
         protocol: TCP
         targetPort: {}""".format(solutionairflowport,solutionairflowport,solutionvipervizport,solutionvipervizport,solutionexternalport,solutionexternalport)
        
    kcmd="""
     apiVersion: apps/v1
     kind: Deployment
     metadata:
       name: {}
     spec:
       selector:
         matchLabels:
           app: {}
       replicas: 3 # tells deployment to run 1 pods matching the template
       template:
         metadata:
           labels:
             app: {}
         spec:
           containers:
           - name: {}
             image: {}
            volumeMounts:
            - name: dockerpath
              mountPath: /var/run/docker.sock
            ports:
        {}
            env:
            - name: TSS
              value: '0'
            - name: SOLUTIONNAME
              value: '{}'
            - name: SOLUTIONDAG
              value: '{}'
            - name: GITUSERNAME
              value: '{}'
            - name: GITREPOURL
              value: '{}'
            - name: SOLUTIONEXTERNALPORT
              value: '{}'
            - name: CHIP
              value: '{}'
            - name: SOLUTIONAIRFLOWPORT
              value: '{}'
            - name: SOLUTIONVIPERVIZPORT
              value: '{}'
            - name: DOCKERUSERNAME
              value: '{}'
            - name: CLIENTPORT
              value: '{}
            - name: EXTERNALPORT
              value: '{}'
            - name: KAFKACLOUDUSERNAME
              value: '{}'
            - name: VIPERVIZPORT
              value: '{}'
            - name: MQTTUSERNAME
              value: '{}'
            - name: AIRFLOWPORT
              value: '{}'
            - name: GITPASSWORD
              value: '<ENTER GITHUB PASSWORD>'
            - name: KAFKACLOUDPASSWORD
              value: '<Enter API secret>'
            - name: MQTTPASSWORD
              value: '<ENTER MQTT PASSWORD>'
            - name: READTHEDOCS
              value: '<ENTER READTHEDOCS TOKEN>'
            - name: qip 
              value: 'privategpt-service' # This is private GPT service in kubernetes              
            - name: KUBE
              value: '1'
          volumes: 
          - name: dockerpath
            hostPath:
              path: /var/run/docker.sock
     ---
     apiVersion: v1
     kind: Service
     metadata:
       name: {}
       labels:
         app: {}
     spec:
       type: NodePort #Exposes the service as a node ports
       ports:
     {}
       selector:
         app: {}""".format(sname,sname,sname,sname,containername,cp,sname,sdag,guser,grepo,solutionexternalport,chip,solutionairflowport,solutionvipervizport,dockerusername,cpp,externalport,kuser,vipervizport,mqttuser,airflowport,sname,sname,cs,sname)  

    return kcmd

def getqip():
    subprocess.call("/tmux/qip.sh", shell=True)
    time.sleep(3)
    with open("/tmux/qip.txt", "r") as file1:
    # Reading from a file
     qip=file1.read()
     qip=qip.rstrip()
     os.environ['qip']=qip  
        
def testvizconnection(portnum):
   good = 1
   #subprocess.call("curl localhost:{} &> /tmux/c.txt".format(portnum), shell=True)
   v=subprocess.run("curl localhost:{} &> /tmux/c.txt".format(portnum), shell = True, executable="/bin/bash")
   print("curl localhost:{} &> /tmux/c.txt".format(portnum), v)
    
   with open('/tmux/c.txt', 'r') as file:
    # Read each line in the file
        for line in file:
        # Print each line
          ls=line.strip()
          if 'Failed to connect' in ls:
            good=0
            break
   return good         

def testtmlconnection():
    good = 1
    if os.environ['SOLUTIONVIPERVIZPORT'] != "":
      subprocess.call("curl localhost:{} &> /tmux/c.txt".format(os.environ['SOLUTIONVIPERVIZPORT']), shell=True)
    # Open the file in read mode
      with open('/tmux/c.txt', 'r') as file:
    # Read each line in the file
        for line in file:
        # Print each line
          ls=line.strip()
          if 'Failed to connect' in ls:
            good=0
            subprocess.call(["tmux", "kill-window", "-t", "viper-produce"])             
            subprocess.call(["tmux", "kill-window", "-t", "viper-preprocess"])             
            subprocess.call(["tmux", "kill-window", "-t", "viper-preprocess2"])             
            subprocess.call(["tmux", "kill-window", "-t", "viper-preprocess-pgpt"])             
            subprocess.call(["tmux", "kill-window", "-t", "viper-predict"])             
            subprocess.call(["tmux", "kill-window", "-t", "viper-ml"])             
            subprocess.call(["tmux", "kill-window", "-t", "hpde-ml"])             
            subprocess.call(["tmux", "kill-window", "-t", "hpde-predict"])                         
            break
            
    return good

def killport(p):
#    p1=int(os.environ['SOLUTIONEXTERNALPORT'])
#    p2=int(os.environ['SOLUTIONVIPERVIZPORT'])
    v=subprocess.call("kill -9 $(lsof -i:{} -t)".format(p), shell=True)  
    
def tmuxchange(tmuxname):
  with open("/tmux/tmux-airflow.sh", "a") as myfile:
    myfile.write("airflow dags trigger {}".format(tmuxname))
    
def getip(viperhost):
    hostname = socket.gethostname()
    IPAddr = socket.gethostbyname(hostname)
    
    if IPAddr == "":
        IPAddr="127.0.0.1"
    if viperhost != "0.0.0.0":
        IPAddr=viperhost
        
    return hostname,IPAddr 

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

def locallogs(mtype,message):    
  
  now = datetime.datetime.now(timezone.utc)
  dbuf = "[{} ".format(mtype) + now.strftime("%Y-%m-%d_%H:%M:%S") + "]"

  with open("/dagslocalbackup/logs.txt", "a") as myfile:
    myfile.write("  {} {}\n\n".format(dbuf,message))
    
    
def git_push2(solution):
    gitpass = os.environ['GITPASSWORD']
    gituser = os.environ['GITUSERNAME']
    
    subprocess.call(["git", "remote", "set-url", "--push", "origin","https://{}@github.com/{}/{}.git".format(gitpass,gituser,solution)])
    
    
def git_push(repopath,message,sname):
    sname=getrepo()
    subprocess.call("/tmux/gitp.sh {} {}".format(sname,message), shell=True)
    
#    try:
 #       repo = Repo(repopath)
  #      repo.git.add(update=True)
   #     repo.index.commit(message)
    #    origin = repo.remote(name=sname)
     #   origin.push()
   # except:
    #    print('Some error occured while pushing the code') 
        #git push -f origin main
     #   os.chdir("/{}".format(repopath))
      #  subprocess.call("git push -f {} main".format(sname), shell=True)
        

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
