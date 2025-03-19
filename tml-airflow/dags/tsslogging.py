# TSS Logging

import datetime
from datetime import timezone 
from git import Repo
import socketserver
import subprocess
import os
import socket
import time
import fcntl

class LockDirectory(object):
    def __init__(self, directory):
        #assert os.path.exists(directory)
        self.directory = directory
        print(self.directory)

    def __enter__(self):
        self.dir_fd = os.open(self.directory, os.O_RDONLY)
        try:
            fcntl.flock(self.dir_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except IOError as ex:             
            raise Exception('Somebody else is locking %r - quitting.' % self.directory)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):       
        fcntl.flock(self.dir_fd,fcntl.LOCK_UN)
        os.close(self.dir_fd)

def rtdsolution(pname,did):
# this is needed if user copies a project from another user to create readthedocs documentation url
        dTOKEN = os.environ['READTHEDOCS'][:4]
        sname=pname
        sd = did
        sdm=''
        if 'solution_preprocessing_dag-' not in sd:  #normal dag solution
             if 'solution_preprocessing_dag_' in sd:
                 sdm = sd[27:len(sd)-len(sname)-1]
                 sname = "{}-{}".format(sname,sdm)
             else:    
                 sdm = sd[23:len(sd)-len(sname)-5]
                 sname = "{}-{}".format(sname,sdm)

        if dTOKEN not in sname:
             sname = "{}-{}".format(sname,dTOKEN)

        if not os.path.isdir("/{}".format(sname)):     
            command="/tmux/rtdprojects.sh {}".format(sname) 
            ret = subprocess.run(command, shell=True)
            time.sleep(5)
        #sname=sname.replace("_","-")
        return sname
    
def ingress(sname):
    
  ing = """
    ############# nginx-ingress-{}.yml
    apiVersion: networking.k8s.io/v1
    kind: Ingress
    metadata:
      name: tml-ingress
      annotations:
        nginx.ingress.kubernetes.io/use-regex: "true"
        nginx.ingress.kubernetes.io/rewrite-target: /$2
    spec:
      ingressClassName: nginx
      rules:
        - host: tml.tss
          http:
            paths:
              - path: /viz(/|$)(.*)
                pathType: ImplementationSpecific
                backend:
                  service:
                    name: {}-visualization-service
                    port:
                      number: 80
              - path: /ext(/|$)(.*)
                pathType: ImplementationSpecific
                backend:
                  service:
                    name: {}-external-service
                    port:
                      number: 80                  
    ---
    apiVersion: v1
    kind: ConfigMap
    apiVersion: v1
    metadata:
      name: ingress-nginx-controller
      namespace: ingress-nginx
    data:
      allow-snippet-annotations: "true"
  """.format(sname,sname,sname)

  return ing

def ingressgrpc(sname):
    
  ing = """
    ############# nginx-ingress-{}-grpc.yml
    apiVersion: networking.k8s.io/v1
    kind: Ingress
    metadata:
      name: tml-ingress
      annotations:
        nginx.ingress.kubernetes.io/use-regex: "true"
        nginx.ingress.kubernetes.io/rewrite-target: /$2
    spec:
      ingressClassName: nginx
      rules:
        - host: tml.tss2
          http:
            paths:
              - path: /viz(/|$)(.*)
                pathType: ImplementationSpecific
                backend:
                  service:
                    name: {}-visualization-service
                    port:
                      number: 80
    ---
    apiVersion: networking.k8s.io/v1
    kind: Ingress
    metadata:
      name: tml-ingress-grpc
      annotations:
        nginx.ingress.kubernetes.io/ssl-redirect: "true"
        nginx.ingress.kubernetes.io/backend-protocol: "GRPCS"
        nginx.ingress.kubernetes.io/auth-tls-pass-certificate-to-upstream: "true"
        nginx.ingress.kubernetes.io/ssl-passthrough: "true"
    spec:
      ingressClassName: nginx
      tls:
      - hosts:
        - tml.tss
        secretName: self-tls    
      rules:
        - host: tml.tss
          http:
            paths:
              - path: /
                pathType: Prefix
                backend:
                  service:
                    name: {}-external-service
                    port:
                      number: 443
    ---
    apiVersion: v1
    kind: ConfigMap
    apiVersion: v1
    metadata:
      name: ingress-nginx-controller
      namespace: ingress-nginx
    data:
      allow-snippet-annotations: "true"
      http2: "True"
      use-forwarded-headers: "true"     
  """.format(sname,sname,sname)

  return ing

def ingressnoext(sname): # Localfile being accessed
  ing = """
    ############# nginx-ingress-{}.yml
    apiVersion: networking.k8s.io/v1
    kind: Ingress
    metadata:
      name: tml-ingress
      annotations:
        nginx.ingress.kubernetes.io/use-regex: "true"
        nginx.ingress.kubernetes.io/rewrite-target: /$2
    spec:
      ingressClassName: nginx
      rules:
        - host: tml.tss
          http:
            paths:
              - path: /viz(/|$)(.*)
                pathType: ImplementationSpecific
                backend:
                  service:
                    name: {}-visualization-service
                    port:
                      number: 80
    ---
    apiVersion: v1
    kind: ConfigMap
    apiVersion: v1
    metadata:
      name: ingress-nginx-controller
      namespace: ingress-nginx
    data:
      allow-snippet-annotations: "true"
  """.format(sname,sname,sname)

  return ing

def genkubeyaml(sname,containername,clientport,solutionairflowport,solutionvipervizport,solutionexternalport,sdag,
                guser,grepo,chip,dockerusername,externalport,kuser,mqttuser,airflowport,vipervizport,
                step4maxrows,step4bmaxrows,step5rollbackoffsets,step6maxrows,step1solutiontitle,step1description,
                step9rollbackoffset,kubebroker,kafkabroker,producetype,step9prompt='',step9context='',step9keyattribute='',step9keyprocesstype='',
                step9hyperbatch='',step9vectordbcollectionname='',step9concurrency='',cudavisibledevices='',step9docfolder='',
                step9docfolderingestinterval='',step9useidentifierinprompt='',step5processlogic='',step5independentvariables='',
                step9searchterms='',step9streamall='',step9temperature='',step9vectorsearchtype='',step9llmmodel='',step9embedding='',
                step9vectorsize='',step4cmaxrows='',step4crawdatatopic='',step4csearchterms='',step4crememberpastwindows='',
                step4cpatternwindowthreshold='',step4crtmsstream='',projectname='',step4crtmsscorethreshold='',step4cattackscorethreshold='',
                step4cpatternscorethreshold='',step4clocalsearchtermfolder='',step4clocalsearchtermfolderinterval='',step4crtmsfoldername=''):
               
    cp = ""
    cpp = ""
    if 'gRPC' in producetype:
        mport='443'
    else:
        mport='80'
      
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
        cp = """    - containerPort: {}
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
             image: {}:latest
             volumeMounts:
             - name: dockerpath
               mountPath: /var/run/docker.sock
             ports:
         {}
             env:
             - name: TSS
               value: '0'
             - name: PROJECTNAME
               value: '{}'               
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
               value: '{}'
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
               valueFrom:
                 secretKeyRef:
                  name: tmlsecrets 
                  key: githubtoken                       
             - name: KAFKACLOUDPASSWORD
               valueFrom:
                 secretKeyRef:
                  name: tmlsecrets 
                  key: kafkacloudpassword                      
             - name: MQTTPASSWORD
               valueFrom: 
                 secretKeyRef:
                   name: tmlsecrets 
                   key: mqttpass                        
             - name: READTHEDOCS
               valueFrom:
                 secretKeyRef:
                   name: tmlsecrets 
                   key: readthedocs          
             - name: qip 
               value: 'privategpt-service' # This is private GPT service in kubernetes
             - name: KUBE
               value: '1'
             - name: step4maxrows # STEP 4 maxrows field can be adjusted here.  Higher the number more data to process, BUT more memory needed.
               value: '{}'
             - name: step4bmaxrows # STEP 4b maxrows field can be adjusted here.  Higher the number more data to process, BUT more memory needed.
               value: '{}'
             - name: step4cmaxrows # STEP 4c maxrows field can be adjusted here.  Higher the number more data to process, BUT more memory needed.
               value: '{}'
             - name: step4crawdatatopic # STEP 4c
               value: '{}'               
             - name: step4csearchterms # STEP 4c 
               value: '{}'
             - name: step4crememberpastwindows # STEP 4c 
               value: '{}'
             - name: step4cpatternwindowthreshold # STEP 4c 
               value: '{}'
             - name: step4crtmsscorethreshold # STEP 4c 
               value: '{}'
             - name: step4cattackscorethreshold # STEP 4c 
               value: '{}'
             - name: step4cpatternscorethreshold # STEP 4c 
               value: '{}' 
             - name: step4crtmsstream # STEP 4c 
               value: '{}'                              
             - name: step4clocalsearchtermfolder # STEP 4c 
               value: '{}'                              
             - name: step4clocalsearchtermfolderinterval # STEP 4c 
               value: '{}'                                             
             - name: step4crtmsfoldername # STEP 4c 
               value: '{}'                                                                                          
             - name: step5rollbackoffsets # STEP 5 rollbackoffsets field can be adjusted here.  Higher the number more training data to process, BUT more memory needed.
               value: '{}'                  
             - name: step5processlogic # STEP 5 processlogic field can be adjusted here.  
               value: '{}'                                 
             - name: step5independentvariables # STEP 5 independent variables can be adjusted here.  
               value: '{}'                                                               
             - name: step6maxrows # STEP 6 maxrows field can be adjusted here.  Higher the number more predictions to make, BUT more memory needed.
               value: '{}'                              
             - name: step9rollbackoffset # STEP 9 rollbackoffset field can be adjusted here.  Higher the number more information sent to privateGPT, BUT more memory needed.
               value: '{}'                                             
             - name: step9prompt # STEP 9 Enter PGPT prompt
               value: '{}'                  
             - name: step9context # STEP 9 Enter PGPT context
               value: '{}'             
             - name: step9keyattribute
               value: '{}' # Step 9 key attribtes change as needed  
             - name: step9keyprocesstype
               value: '{}' # Step 9 key processtypes change as needed                                
             - name: step9hyperbatch
               value: '{}' # Set to 1 if you want to batch all of the hyperpredictions and sent to chatgpt, set to 0, if you want to send it one by one   
             - name: step9vectordbcollectionname
               value: '{}'   # collection name in Qdrant
             - name: step9concurrency # privateGPT concurency, if greater than 1, multiple PGPT will run
               value: '{}'
             - name: CUDA_VISIBLE_DEVICES
               value: '{}' # 0 for any device or specify specific number 
             - name: step9docfolder # privateGPT docfolder to load files in Qdrant vectorDB local context
               value: '{}'
             - name: step9docfolderingestinterval # privateGPT docfolderingestinterval, number of seconds to wait before reloading files in docfolder
               value: '{}'
             - name: step9useidentifierinprompt # privateGPT useidentifierinprompt, if 1, add TML output json field Identifier, if 0 use prompt
               value: '{}'               
             - name: step9searchterms # privateGPT searchterms, terms to search for in the chat response
               value: '{}'                              
             - name: step9streamall # privateGPT streamall, if 1, stream all responses, even if search terms are missing, 0, if response contains search terms
               value: '{}'                                             
             - name: step9temperature # privateGPT LLM temperature between 0 and 1 i.e. 0.3, if 0, LLM model is conservative, if 1 it hallucinates
               value: '{}'                                             
             - name: step9vectorsearchtype # privateGPT for QDrant VectorDB similarity search.  Must be either Cosine, Manhattan, Dot, Euclid
               value: '{}'                                                            
             - name: step1solutiontitle # STEP 1 solutiontitle field can be adjusted here. 
               value: '{}'                              
             - name: step1description # STEP 1 description field can be adjusted here. 
               value: '{}'        
             - name: step1rtmsmaxwindows # STEP 1 adjust RTMSMAXWINDOWS for Step 4c
               value: '10000'                        
             - name: KUBEBROKERHOST
               value: '{}'         
             - name: KAFKABROKERHOST
               value: '{}'                              
           volumes: 
           - name: dockerpath
             hostPath:
               path: /var/run/docker.sock
   ---
     apiVersion: v1
     kind: Service
     metadata:
       name: {}-visualization-service
       labels:
         app: {}-visualization-service
     spec:
       type: ClusterIP
       ports:
       - port: 80 # Ingress port, if using port 443 will need to setup TLS certs
         name: p1
         protocol: TCP
         targetPort: {}
       selector:
         app: {}
   ---
     apiVersion: v1
     kind: Service
     metadata:
       name: {}-external-service
       labels:
         app: {}-external-service
     spec:
       type: ClusterIP
       ports:
       - port: {} # Ingress port, if using port 443 will need to setup TLS certs
         name: p2
         protocol: TCP
         targetPort: {}
       selector:
         app: {}""".format(sname,sname,sname,sname,containername,cp,projectname,sname,sdag,guser,grepo,solutionexternalport,chip,solutionairflowport,solutionvipervizport,dockerusername,cpp,externalport,kuser,vipervizport,mqttuser,
                           airflowport,step4maxrows,step4bmaxrows,step4cmaxrows,step4crawdatatopic,step4csearchterms,step4crememberpastwindows,step4cpatternwindowthreshold,
                           step4crtmsscorethreshold,step4cattackscorethreshold,step4cpatternscorethreshold,step4crtmsstream,step4clocalsearchtermfolder,step4clocalsearchtermfolderinterval,step4crtmsfoldername,
                           step5rollbackoffsets,step5processlogic,step5independentvariables,step6maxrows,step9rollbackoffset,
                           step9prompt,step9context,step9keyattribute,step9keyprocesstype,step9hyperbatch,step9vectordbcollectionname,step9concurrency,cudavisibledevices,
                           step9docfolder,step9docfolderingestinterval,step9useidentifierinprompt,step9searchterms,step9streamall,step9temperature,step9vectorsearchtype,
                           step1solutiontitle,step1description,kubebroker,kafkabroker,
                           sname,sname,solutionvipervizport,sname,sname,sname,mport,cpp,sname)
                    
    return kcmd

def genkubeyamlnoext(sname,containername,clientport,solutionairflowport,solutionvipervizport,solutionexternalport,sdag,
                     guser,grepo,chip,dockerusername,externalport,kuser,mqttuser,airflowport,vipervizport,
                     step4maxrows,step4bmaxrows,step5rollbackoffsets,step6maxrows,step1solutiontitle,step1description,
                     step9rollbackoffset,kubebroker,kafkabroker,step9prompt='',step9context='',step9keyattribute='',step9keyprocesstype='',
                     step9hyperbatch='',step9vectordbcollectionname='',step9concurrency='',cudavisibledevices='',step9docfolder='',
                     step9docfolderingestinterval='',step9useidentifierinprompt='',step5processlogic='',step5independentvariables='',
                     step9searchterms='',step9streamall='',step9temperature='',step9vectorsearchtype='',step9llmmodel='',step9embedding='',step9vectorsize='',
                     step4cmaxrows='',step4crawdatatopic='',step4csearchterms='',step4crememberpastwindows='',
                     step4cpatternwindowthreshold='',step4crtmsstream='',projectname='',step4crtmsscorethreshold='',step4cattackscorethreshold='',
                     step4cpatternscorethreshold='',step4clocalsearchtermfolder='',step4clocalsearchtermfolderinterval='',step4crtmsfoldername=''):
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
        cp = """    - containerPort: {}
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
             image: {}:latest
             volumeMounts:
             - name: dockerpath
               mountPath: /var/run/docker.sock
             ports:
         {}
             env:
             - name: TSS
               value: '0'
             - name: PROJECTNAME
               value: '{}'                              
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
               value: '{}'
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
               valueFrom:
                 secretKeyRef:
                  name: tmlsecrets 
                  key: githubtoken                       
             - name: KAFKACLOUDPASSWORD
               valueFrom:
                 secretKeyRef:
                  name: tmlsecrets 
                  key: kafkacloudpassword                      
             - name: MQTTPASSWORD
               valueFrom: 
                 secretKeyRef:
                   name: tmlsecrets 
                   key: mqttpass                        
             - name: READTHEDOCS
               valueFrom:
                 secretKeyRef:
                   name: tmlsecrets 
                   key: readthedocs          
             - name: qip 
               value: 'privategpt-service' # This is private GPT service in kubernetes
             - name: KUBE
               value: '1'
             - name: step4maxrows # STEP 4 maxrows field can be adjusted here.  Higher the number more data to process, BUT more memory needed.
               value: '{}'
             - name: step4bmaxrows # STEP 4b maxrows field can be adjusted here.  Higher the number more data to process, BUT more memory needed.
               value: '{}'               
             - name: step4cmaxrows # STEP 4c maxrows field can be adjusted here.  Higher the number more data to process, BUT more memory needed.
               value: '{}'               
             - name: step4crawdatatopic # STEP 4c
               value: '{}'               
             - name: step4csearchterms # STEP 4c 
               value: '{}'               
             - name: step4crememberpastwindows # STEP 4c 
               value: '{}'               
             - name: step4cpatternwindowthreshold # STEP 4c 
               value: '{}'               
             - name: step4crtmsscorethreshold # STEP 4c 
               value: '{}' 
             - name: step4cattackscorethreshold # STEP 4c 
               value: '{}' 
             - name: step4cpatternscorethreshold # STEP 4c 
               value: '{}'                
             - name: step4crtmsstream # STEP 4c 
               value: '{}'                              
             - name: step4clocalsearchtermfolder # STEP 4c 
               value: '{}'                              
             - name: step4clocalsearchtermfolderinterval # STEP 4c 
               value: '{}'                                                            
             - name: step4crtmsfoldername # STEP 4c 
               value: '{}'                                                                           
             - name: step5rollbackoffsets # STEP 5 rollbackoffsets field can be adjusted here.  Higher the number more training data to process, BUT more memory needed.
               value: '{}'                              
             - name: step5processlogic # STEP 5 processlogic field can be adjusted here.  
               value: '{}'                                                
             - name: step5independentvariables # STEP 5 independent variables can be adjusted here.  
               value: '{}'                                                                              
             - name: step6maxrows # STEP 6 maxrows field can be adjusted here.  Higher the number more predictions to make, BUT more memory needed.
               value: '{}'                              
             - name: step9rollbackoffset # STEP 9 rollbackoffset field can be adjusted here.  Higher the number more information sent to privateGPT, BUT more memory needed.
               value: '{}'                  
             - name: step9prompt # STEP 9 Enter PGPT prompt
               value: '{}'                  
             - name: step9context # STEP 9 Enter PGPT context
               value: '{}'                                 
             - name: step9keyattribute
               value: '{}' # Step 9 key attribtes change as needed  
             - name: step9keyprocesstype
               value: '{}' # Step 9 key processtypes change as needed                                               
             - name: step9hyperbatch
               value: '{}' # Set to 1 if you want to batch all of the hyperpredictions and sent to chatgpt, set to 0, if you want to send it one by one   
             - name: step9vectordbcollectionname
               value: '{}'   # collection name in Qdrant
             - name: step9concurrency # privateGPT concurency, if greater than 1, multiple PGPT will run
               value: '{}'
             - name: CUDA_VISIBLE_DEVICES
               value: '{}' # 0 for any device or specify specific number                
             - name: step9docfolder # privateGPT docfolder to load files in Qdrant vectorDB local context
               value: '{}'
             - name: step9docfolderingestinterval # privateGPT docfolderingestinterval, number of seconds to wait before reloading files in docfolder
               value: '{}'
             - name: step9useidentifierinprompt # privateGPT useidentifierinprompt, if 1, add TML output json field Identifier, if 0 use prompt
               value: '{}'                              
             - name: step9searchterms # privateGPT searchterms, terms to search for in the chat response
               value: '{}'                                             
             - name: step9streamall # privateGPT streamall, if 1, stream all responses, even if search terms are missing, 0, if response contains search terms
               value: '{}'                                                            
             - name: step9temperature # privateGPT LLM temperature between 0 and 1 i.e. 0.3, if 0, LLM model is conservative, if 1 it hallucinates
               value: '{}'                                             
             - name: step9vectorsearchtype # privateGPT for QDrant VectorDB similarity search.  Must be either Cosine, Manhattan, Dot, Euclid
               value: '{}'                                                                           
             - name: step1solutiontitle # STEP 1 solutiontitle field can be adjusted here. 
               value: '{}'                              
             - name: step1description # STEP 1 description field can be adjusted here. 
               value: '{}'                                          
             - name: step1rtmsmaxwindows # STEP 1 adjust RTMSMAXWINDOWS for Step 4c
               value: '10000'                                       
             - name: KUBEBROKERHOST
               value: '{}'         
             - name: KAFKABROKERHOST
               value: '{}'                              
           volumes: 
           - name: dockerpath
             hostPath:
               path: /var/run/docker.sock
   ---
     apiVersion: v1
     kind: Service
     metadata:
       name: {}-visualization-service
       labels:
         app: {}-visualization-service
     spec:
       type: ClusterIP
       ports:
       - port: 80 # Ingress port, if using port 443 will need to setup TLS certs
         name: p1
         protocol: TCP
         targetPort: {}
       selector:
         app: {}""".format(sname,sname,sname,sname,containername,cp,projectname,sname,sdag,guser,grepo,solutionexternalport,chip,solutionairflowport,solutionvipervizport,dockerusername,cpp,externalport,kuser,vipervizport,
                           mqttuser,airflowport,step4maxrows,step4bmaxrows,step4cmaxrows,step4crawdatatopic,step4csearchterms,step4crememberpastwindows,step4cpatternwindowthreshold,
                           step4crtmsscorethreshold,step4cattackscorethreshold,step4cpatternscorethreshold,step4crtmsstream,step4clocalsearchtermfolder,step4clocalsearchtermfolderinterval,step4crtmsfoldername,
                           step5rollbackoffsets,step5processlogic,step5independentvariables,step6maxrows,step9rollbackoffset,
                           step9prompt,step9context,step9keyattribute,step9keyprocesstype,step9hyperbatch,step9vectordbcollectionname,step9concurrency,cudavisibledevices,
                           step9docfolder,step9docfolderingestinterval,step9useidentifierinprompt,step9searchterms,step9streamall,step9temperature,step9vectorsearchtype,
                           step1solutiontitle,step1description,kubebroker,kafkabroker,
                           sname,sname,solutionvipervizport,sname)
                    
    return kcmd

def getqip():
    subprocess.call("/tmux/qip.sh", shell=True)
    time.sleep(3)
    with open("/tmux/qip.txt", "r") as file1:
    # Reading from a file
     qip=file1.read()
     qip=qip.rstrip()
     os.environ['qip']=qip  
        
def optimizecontainer(cname,sname,sd):
    rbuf=os.environ['READTHEDOCS']
    buf="docker run -d -v /var/run/docker.sock:/var/run/docker.sock:z --env GPG_KEY='' --env PYTHON_SHA256='' --env DOCKERUSERNAME='{}' --env SOLUTIONNAME={} --env SOLUTIONDAG={} --env TSS=-9  --env READTHEDOCS='{}' --env MQTTPASSWORD='' --env DOCKERPASSWORD=''  --env  GITPASSWORD='' --env KAFKACLOUDPASSWORD='' {}".format(os.environ['DOCKERUSERNAME'], sname, sd, rbuf[:4],cname )
    
    print("Container optimizing: {}".format(buf))
    subprocess.call(buf, shell=True)

    i=0
    exists=0
    ret=-1
    status=""
    while True:
      i = i + 1  
      time.sleep(5)          
    
      if i > 90:
         print("WARN: Unable to optimize container")
         break
        
      try:  
       # cname2="{}sq".format(cname)  
        greps="docker ps"
        ret=subprocess.check_output(greps, shell=True)        
        ret=ret.decode("utf-8")
        ret=ret.strip()
        if cname not in ret:
          print("INFO: Container optimized")  
          status="good"
          break
        
      except Exception as e:
         print("ERROR: ",e)
         continue
            
    buf="docker image tag  {}sq:latest  {}".format(cname,cname)
    print("Docker image tag: {}".format(buf))
    subprocess.call(buf, shell=True)
    time.sleep(3)
    buf="docker rmi {}sq:latest --force".format(cname)
    print("Docker image rmi: {}".format(buf))
        
    subprocess.call(buf, shell=True)
    subprocess.call("docker rmi -f $(docker images --filter 'dangling=true' -q --no-trunc)", shell=True)
    return status
    
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
            subprocess.call(["tmux", "kill-window", "-t", "viper-preprocess3"])                           
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
  try:
    with open("/dagslocalbackup/logs.txt", "a") as myfile:
      myfile.write("  {} {}\n\n".format(dbuf,message))
  except Exception as e:
      print("WARN: Cannot write to /dagslocalbackup/logs.txt:",e)
    
    
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
