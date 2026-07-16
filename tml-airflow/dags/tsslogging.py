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
import json
from pypdf import PdfWriter
import re
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor
import math
import maadstml
import sys
from collections import Counter
import traceback

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

def writeoutymls(op,ingyml,solyml,sname):
#                kcmd = "kubectl apply -f kafka.yml -f secrets.yml -f mysql-storage.yml -f mysql-db-deployment.yml -f qdrant.yml -f privategpt.yml -f ollama.yml -f {}.yml".format(sname)
  file_name=f"{op}/ingress.yml"
  with open(file_name, "w") as file:
    file.write(ingyml)

  file_name=f"{op}/{sname}.yml"
  with open(file_name, "w") as file:
    file.write(solyml)
  
  ing="""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kafka
spec:
  selector:
    matchLabels:
      app: kafka
  replicas: 1 # tells deployment to run 1 pods matching the template
  template:
    metadata:
      labels:
        app: kafka
    spec:
      containers:
      - name: kafka
        image: maadsdocker/kafka-amd64  # IF you DO NOT have NVIDIA GPU use: maadsdocker/tml-privategpt-no-gpu-amd64
        env:
        - name: KAFKA_HEAP_OPTS
          value: "-Xmx512M -Xms512M"
        - name: PORT
          value: "9092"
        - name: TSS
          value: "0"
        - name: KUBE
          value: "1"
        - name: KUBEBROKERHOST
          value: "kafka-service:9092"
---
apiVersion: v1
kind: Service
metadata:
  name: kafka-service
spec:
  ports:
  - port: 9092
  selector:
    app: kafka  
  """
  file_name=f"{op}/kafka.yml"
  with open(file_name, "w") as file:
    file.write(ing)

  ing="""
########## NOTE: tls certs are for tml.tss server only
# You can replace tls.crt and tls.key with your own server.crt and server.key
#############secret-tls.yml
apiVersion: v1
data:
  tls.crt: LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCk1JSUY5ekNDQTkrZ0F3SUJBZ0lVWFlPeUJia21qaUxMMDFiMkI2NVI5UllHbVNBd0RRWUpLb1pJaHZjTkFRRUwKQlFBd1ZURUxNQWtHQTFVRUJoTUNRMEV4RURBT0JnTlZCQWdNQjA5dWRHRnlhVzh4RURBT0JnTlZCQWNNQjFSdgpjbTl1ZEc4eERqQU1CZ05WQkFvTUJVOTBhV056TVJJd0VBWURWUVFEREFsVFpXSmhjM1JwWVc0d0lCY05NalF4Ck1qRTVNVFF4T1RJeldoZ1BNakV5TkRFeE1qVXhOREU1TWpOYU1GVXhDekFKQmdOVkJBWVRBa05CTVJBd0RnWUQKVlFRSURBZFBiblJoY21sdk1SQXdEZ1lEVlFRSERBZFViM0p2Ym5Sdk1RNHdEQVlEVlFRS0RBVlBkR2xqY3pFUwpNQkFHQTFVRUF3d0pVMlZpWVhOMGFXRnVNSUlDSWpBTkJna3Foa2lHOXcwQkFRRUZBQU9DQWc4QU1JSUNDZ0tDCkFnRUE3SEdwMFVVV2toejIzWVpRWE41VEVSR3JHYk43RzdQRWI3dEtRTWFObUtkVmFRQjlpRmVqQ3ZtUWxYNXUKcjZjMjF6VkMrVC8zZ0lQZmN3bW9SNzVDZGQ4dDhYRkVIOXRFSVBsZXYrbzVRNzFHajRqdnh1YTBBeU1KQlVuRwpNeEZTT2Qxek9heVlGSDFNMk94R0RUOU1RT3liZEFLd3pGU2YyZHlDcUx3cW0rWTJjWlIrbkFWOS81T1RaOVhiCktmVjJwWFNyRjVhcGovQTFCL3lDTlpDb284Nit4bFBFajRISGhxV1NvVkZxT1dhMlZ4dC9UQjlnKzFyL2hGOWEKV2g5UTZZNmRtK1FYUnhaWGxZR1pzdGVmbjFCcmY2cHdrWTRJZmtPd3RCb29EUnhUajg5U213bjdwaDJQczdFMQpvU2NoYkVkSDZLSjIxZ3JVSXEwZFMzaEZES2pYL2UrT2xIclk1bE42UmJqLzAwUjVhenRMcXFQWjFGNVdBTHNsCnp5MzV2SHNoR2dzVVRNVGVZLzQ1RmpMamJrLzdMckdOZWlhQUZXcFkrb0oyTUF6ZUN1QnlRRW95OWhrLzVjNTUKS0IyMVNzdU02M3Q0bElQV0VGNFBrbUFGNHFDNEZOMldLQ2E2RTgyWTFsdmxYQmNHL2dZalZ0ZTdmTzdaLy9MRQp6Vk5tOHJqRGVXTUR6eEdTYzIvVXQ3QzJKVkF6VlRlWmZ5Vm9TZWtMZmZ1S1FreWxRUERHMGVQRXR6UEEyYjI3CkE1dTdsaThaV1RMUEs3WW0xTXNPOHN5ZmNmTTI1c0had2pDVVBOdzNhbXl6blRtLzhtb2FheVR2RWZZaTlIVjYKejlNY3Y1dlltdFhDaDZxSm00RHNLbmdGMkNrd29DMldmQjRjVjRvRDE2RStETGNDQXdFQUFhT0J2RENCdVRBYwpCZ05WSFJFRUZUQVRnZ2QwYld3dWRITnpnZ2gwYld3dWRITnpNakFkQmdOVkhRNEVGZ1FVVVZ2aE5zS3RHaURVCkFQTXo0Ni8wV2s0QkpuWXdlZ1lEVlIwakJITXdjYUZacEZjd1ZURUxNQWtHQTFVRUJoTUNRMEV4RURBT0JnTlYKQkFnTUIwOXVkR0Z5YVc4eEVEQU9CZ05WQkFjTUIxUnZjbTl1ZEc4eERqQU1CZ05WQkFvTUJVOTBhV056TVJJdwpFQVlEVlFRRERBbFRaV0poYzNScFlXNkNGQk5aVGFPVStaQlVDa29LVVJzZ2o3QVN0ZFBzTUEwR0NTcUdTSWIzCkRRRUJDd1VBQTRJQ0FRQjAwUThodVJ2d3RvTzFkQjZKRzBHTjE1bXJGYUhyRlR4dnU3RFlPK0xWc2RtQmxoNVoKUFFSUVdjUUZaeFRvVmJZbldPY2hmY1VMK3padVo2QVdQOVp4RHljWjNrT3JFUm9EbjJzL0wzSk5sK0IyRGhmUQpwUytMeWdLMWt6RGhEeWI2dE0rSVdTRzY2RWdIZHF0U0dDM2czWXR0eTNEZTZidzFzSERwTkg3Q08wNndId1Y4CkdCVC9PempoS2U2M3RyaGxZZmtvM1IrQnFQTWd0YlN4MTlOOVBBY0FRbFgrQVJEckJ5a2tZZkExVVpKcml5aHQKRllZNXdmcmpJcTB5N0RtSDBYVkwxRkhNKzFCdFJrcnJxU1pSWHYybjRlTnFuMlRiUjZpdTdWS0pjdnVCYkYrMwpMRDdEZDBjdjRYSmxxektyUWtWR0R5T3M2bVMvcEhPcVhMNmNOREdpc1BpSFRRWkppcEFaUFpQQ3pXUjdjam1WCmkyVmZMN3NPTmlReXY5WFIyYzYrQndFbXk3bDg1dnBmVG9VaHN2R1lMemJjcndDM1lOL0d1WnQzQW5EQ1cyT04KV05lcldSTmhrYjFSdUFtWVREY21jb0t0OSt2RFY1M2NtK1BJUno1ZldhUUNXYjhXdDFuMjFkNitoRWtBdVcxRQppQmh0RFJYcy8xeUkxOEI1UlFGSU44ZkNQMnh5WWR1b0MzbldnTUR5NzRkcUNsT0hlTmhEUFIyM3NZNjR4bmhKCkRBcHh2dTBwT3crTno2bjcyU0o4Ky9TODlaRW1jQy9nWFNnOVZ0SEYzNDR6YzVma3ZiMFZyWDRqVHA3R1JLSTEKRlZOWkRBbml3TXN5eGJnUEJEMGEwb1gwTlY0OEJUTkdaTzNWRzVLdVpwN3BXYmxseHh6QldHWnVvZz09Ci0tLS0tRU5EIENFUlRJRklDQVRFLS0tLS0K
  tls.key: LS0tLS1CRUdJTiBQUklWQVRFIEtFWS0tLS0tCk1JSUpRd0lCQURBTkJna3Foa2lHOXcwQkFRRUZBQVNDQ1Mwd2dna3BBZ0VBQW9JQ0FRRHNjYW5SUlJhU0hQYmQKaGxCYzNsTVJFYXNaczNzYnM4UnZ1MHBBeG8yWXAxVnBBSDJJVjZNSytaQ1ZmbTZ2cHpiWE5VTDVQL2VBZzk5egpDYWhIdmtKMTN5M3hjVVFmMjBRZytWNi82amxEdlVhUGlPL0c1clFESXdrRlNjWXpFVkk1M1hNNXJKZ1VmVXpZCjdFWU5QMHhBN0p0MEFyRE1WSi9aM0lLb3ZDcWI1alp4bEg2Y0JYMy9rNU5uMWRzcDlYYWxkS3NYbHFtUDhEVUgKL0lJMWtLaWp6cjdHVThTUGdjZUdwWktoVVdvNVpyWlhHMzlNSDJEN1d2K0VYMXBhSDFEcGpwMmI1QmRIRmxlVgpnWm15MTUrZlVHdC9xbkNSamdoK1E3QzBHaWdOSEZPUHoxS2JDZnVtSFkrenNUV2hKeUZzUjBmb29uYldDdFFpCnJSMUxlRVVNcU5mOTc0NlVldGptVTNwRnVQL1RSSGxyTzB1cW85blVYbFlBdXlYUExmbThleUVhQ3hSTXhONWoKL2prV011TnVUL3N1c1kxNkpvQVZhbGo2Z25Zd0RONEs0SEpBU2pMMkdUL2x6bmtvSGJWS3k0enJlM2lVZzlZUQpYZytTWUFYaW9MZ1UzWllvSnJvVHpaaldXK1ZjRndiK0JpTlcxN3Q4N3RuLzhzVE5VMmJ5dU1ONVl3UFBFWkp6CmI5UzNzTFlsVUROVk41bC9KV2hKNlF0OSs0cENUS1ZBOE1iUjQ4UzNNOERadmJzRG03dVdMeGxaTXM4cnRpYlUKeXc3eXpKOXg4emJtd2RuQ01KUTgzRGRxYkxPZE9iL3lhaHBySk84UjlpTDBkWHJQMHh5L205aWExY0tIcW9tYgpnT3dxZUFYWUtUQ2dMWlo4SGh4WGlnUFhvVDRNdHdJREFRQUJBb0lDQUQ1UnVSSWsxUTJlMzd4RWpnTGtRRjJqCjNBYVNwVlNJWGJLYldUZFlmZktwekJ1NFd0M29SMXQ1cXMrVU91VkdPL0NlSTdCaFdVRkF3TkRuenpoVm45dkUKZnE0QURoWWRhMGdMb2hzUVI1YWdtU3YweWtvUS9ZcEVIamtNR0ZiV2JtYzlCSVZEaGZRRWtKQXVPa3A4a0FNZQp1ZHhxWnlINy9nUGttSFdUM3VFblhOc3o2ZWtDazVLYzJZSEpQcEpCRmN3SFE1OGNnVVdrYUwzWm9wSXV0aHd5CnZscTBzbjZtbEtuYkV4bzh4TFFyYTh6cXZQTVo1Q3hyOENQNkkrelVDelg3OW5PanV6VHI0UnJSUldyN1pTR1AKQno1bmRITVF6aEZGa3hudE9QZzNxcGloYXVMZFR6d1oxNG5qbjhDQmVWQTZPMnhJQWUxcGZqOURoSkNqT3dOWQo5Y0RsYUEwVXpqOXcxTjdZdjk0RERDWWJIVVJweldQNXQ2TUo4ZFp3eHIxNmV6eG01ejlPaExTZzBzWWx6Z3k0CjA2YlRia2pIMlg1S05tZlNjK05saDh0T2t2QnRVSXgydUZvNkZWRFVhKzRKSUhyNVRtUUZMbS92OE5ha0puZWsKbkF0UGpSL0ZubzNGT1F0Ynpja2xJNVVXaVBHWWczQ3Y3Z3ZqYkVuUXJtT3B5Z3QxcFdWVnpTRnhCWjl1QmRxcgpod01USHlURHFxTDBtaGg4UXhnOGR2NllBR0srR3lSQmU3SDVENTdqVXE0eG5ML20zWVA2SERnV2x0YTg4MTVlCmtlalhkVUcvMk9qVmEwZmNxK2x2d3htRUJ3YXJueGw2VUVpTGhlb1JzSkFaZkl6L1hFMlhxYStnaWpwcDRRbFgKTkxNeXNQNWVYb0JxNXArOUQzZnBBb0lCQVFEN2wrMEx5ZFVkdERCdU5EQ0dUSGhBS1N1Z05HWDZyK2Fady9XOQpyVkZRYWJTdWhjYy9MMmxIUHNsN0NNamZrNVk5b1BxazZUYUJKR0NhMFFBWGc5bTBCR09CMUZhd203Z0F5YlIyCldJWlViaGxybjBBM29zU3J3YUVnc3BZUG5WRTlQOU9GUGdhWWoyd2NNSkVleENRb2t4QmlvOFQwSElGQklWQUUKTGExTmQvcFl0bUNYeGtncjlnWHh3QlpaZlJjbk93V0dkOVBvMDN6Y3NVOWVsSE1kOG1Db1dQbGtGcXBQN2VXKwp5VHo5Q3ovWUgrTTYyWFBOQldJM2VNRWpuMlBaUEp1WnFmcVN4cVcwMWJSdU1lbFgrd1dSeEdHK1hSS3l5cENlCkV4N0xTd3pNdk9QQVVkVVFrT3A0ZEFXZGFQeGNXcUFGVU5Cb1VTY2xGMmtOTlRVL0FvSUJBUUR3bGMrOHBxSDIKV2dtOW83RnltSFhHdldJdmIvMTBpRFpFZ1gzK3dTU1Y5SW5mNEtINDZvM29ER21tTWlYS2R3T1FYenVLTksycgpSSHNOZEl4VG05cnFxa3BNckZGaUplZ3JuTU43VFpON0pnaHE4SkNkR2JUb0xPYTNVTzJSWnRSZ0phOUVPZjhXClFBRmxqeTRnN294ZktudURORWZGNUFzTW5PaTdTWFNQSXpxdDBXMGdZcmdQaGd1YUFGSFIyMzNJRkRkeG02d0sKTGJkSDdmS09QQ1diVEpQVzQvQTRDaks3WVVKWERzUHFmbjBYT2JNWDlWSVNDLzM2M1JqbjQ1S3RuVUtJa2RCRgpIWkxLc1hvOU0wT2ZUb0dTdlNsV0g0SVZmTE81NTlsM2FFVHp2OXZQVzRqcmE1Rkc3TEV6a3FiSXRUWkEyemp2Cmgwa0JRMk4xMGZLSkFvSUJBRGJqckdtMy9QRGdFUGphRmdRV3h0MW9uZ1h6cUpRS3NFcTN2L05EenN1MlpCNzMKUE1NQ092dTZMUWJVb2M1MVNuL2prUXROZmdDcXlSQzlyRUYxR0pmM3BTWDhCM1c4WTJaNG14Qit1Ny9Meld2MwpjSEV5NTZsNU13Z0pMa2YxMEhXR2FVVldoT1hmMUh4SjlEODhGNDlxbGxhTzJEZFJ5TGxHNVVna0Z2MGh3ZEo4CjU1SDFSbVdnNVNjYSswVkd6emhWM2h5Nkk5ZFYzSlhoY1NsM1JhNHc1UG1WZjhOZ1ZvUGRxUlA0bjMrdFpwNW0KUnBMZVFpOW1qMGorNVZRNlAvUnpEcGQxeUI4aGk2RnFSbFVNT3BaaFE1UEx2bTlqcXVLcTR1WTUwYXdVa1pSUgpXWGJwNDR3YnNhdloxQ2ZGY2RsTVJFRWtvbk0vMFVSOFdRVHlxTTBDZ2dFQkFNUUVDMkZWRXBpNCt6NjdaQlJPCkM0ZUZQYjRRckp5SmJrMmFnNkZRbEJKcFR2eE05U3J0VC9sRVE3L1pFOWxGNW0xMmFmaE11MExUWkw2dHVyZFUKUUtUNVlkZmVmZUJOcWovK1ZYYmMyZEI0U0Z0NDdScFNtNGFmTHNzazhLcUs4WFgwdmp3RVZNVTRHT3M2SVFkTAoxS3FrM2tVa0QyWTRTcGhZTDNhSWZxTXd2TnBweTFPYm13TnEzNEQxeWJRRjlSRlRCMmxVd0hMNmxGM1NqTkUrClNCV2o2c0FtcnMyNTRXT3g5bThmNUpmbHZ0MXhjVzJQdnZKZE91MXR2cUVRVmEyR2QzTDErbzZWYmNnZm1jekwKTzhsTUdWNEpLT2kyZXpJdWkvQm42bExUYlhwN1V3ZzdOKzgza1FJTVRzUUtORUZMQTQwTUQvTjRjZzdKYlB2Tgp0cUVDZ2dFQkFNK1Y0VGp3N2xTblQzMUdyNzl6RFQ2bnIrYytOVE96VnBxNG4zcTVnbk5SUklKamN1NkxPRXhvCmRhSVFWZlcxU0hGUVowcXFKYXJoZmZlRnQ0OVd5SW5lcHY4TTJWNmFDMkFZdm1qazhuMHlHcUFqOE1zLzVBTTQKQ1lKRDJ1Tm1EZDI5TkxLTEdFbzNaNFE0c1MrMVY3aXRtbGw5V3lYQWNiUStienAvbEhaa0ZNNzFNUGtuN0ErcwpmOHhUekhYYVR5YjQ2b3pBMmxyQmVFQ2QrMGdyaVZLZG51V2pqT0Z5YldldHIyTXcyR05yWEF6RHpCa21Kc1JTCnhmbVFVSGw2OXlSc0M4Q05Hd3k3VGJxQ3gwOEJ5ZHAzWG9yR1ZyakpRak95Y0p2ODErQkl3V2YrcUp2THlFRWgKbTgvQjN4RkUyTkNITHRmVEtKcVFabDZEQkhXK2xBaz0KLS0tLS1FTkQgUFJJVkFURSBLRVktLS0tLQo=
kind: Secret
metadata:
  creationTimestamp: "2024-12-19T15:56:35Z"
  name: self-tls
  namespace: default
type: kubernetes.io/tls
  """
  
  file_name=f"{op}/secrets-tls.yml"
  with open(file_name, "w") as file:
    file.write(ing)
  ing="""
###################secrets.yml
apiVersion: v1
kind: Secret
metadata:
  name: tmlsecrets
type: Opaque
data:
  readthedocs: <enter your base64 password>
  githubtoken: <enter your base64 password>
  mqttpass: <enter your base64 password>
  kafkacloudpassword: <enter your base64 password>
"""
  file_name=f"{op}/secrets.yml"
  with open(file_name, "w") as file:
    file.write(ing)

  ing="""
################# mysql-storage.yml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: mysql-pv-volume
  labels:
    type: local
spec:
  storageClassName: manual
  capacity:
    storage: 20Gi
  accessModes:
    - ReadWriteMany
  hostPath:
    path: "/mnt/data"
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: mysql-pv-claim
spec:
  storageClassName: manual
  accessModes:
    - ReadWriteMany
  resources:
    requests:
      storage: 20Gi
"""

  file_name=f"{op}/mysql-storage.yml"
  with open(file_name, "w") as file:
    file.write(ing)

  ing="""
################# mysql-db-deployment.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mysql
spec:
  selector:
    matchLabels:
      app: mysql
  strategy:
    type: Recreate
  template:
    metadata:
      labels:
        app: mysql
    spec:
      containers:
      - image: maadsdocker/mysql:latest
        name: mysql
        resources:
         limits:
          memory: "512Mi"
          cpu: "1500m"
        env:
        - name: MYSQL_ROOT_PASSWORD
          value: "raspberry"
        - name: MYSQLDB
          value: "tmlids"
        - name: MYSQLDRIVERNAME
          value: "mysql"
        - name: MYSQLHOSTNAME
          value: "mysql:3306"
        - name: MYSQLMAXCONN
          value: "4"
        - name: MYSQLMAXIDLE
          value: "10"
        - name: MYSQLPASS
          value: "raspberry"
        - name: MYSQLUSER
          value: "root"
        ports:
        - containerPort: 3306
          name: mysql
        volumeMounts:
        - name: mysql-persistent-storage
          mountPath: /var/lib/mysql
      volumes:
      - name: mysql-persistent-storage
        persistentVolumeClaim:
          claimName: mysql-pv-claim

---
apiVersion: v1
kind: Service
metadata:
  name: mysql-service
spec:
  ports:
  - port: 3306
  selector:
    app: mysql
"""

  file_name=f"{op}/mysql-db-deployment.yml"
  with open(file_name, "w") as file:
    file.write(ing)

  ing="""
################# privategpt.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: privategpt
spec:
  selector:
    matchLabels:
      app: privategpt
  replicas: 1 # tells deployment to run 1 pods matching the template
  template:
    metadata:
      labels:
        app: privategpt
    spec:
      containers:
      - name: privategpt
        image: --kubeprivategpt-- # IF you DO NOT have NVIDIA GPU use: maadsdocker/tml-privategpt-no-gpu-amd64
        imagePullPolicy: IfNotPresent  # You can also use Always, Never
        env:
        - name: NVIDIA_VISIBLE_DEVICES
          value: all
        - name: DP_DISABLE_HEALTHCHECKS
          value: xids
        - name: WEB_CONCURRENCY
          value: "--kubeconcur--"
        - name: GPU
          value: "1"
        - name: COLLECTION
          value: "--kubecollection--"
        - name: PORT
          value: "8001"
        - name: CUDA_VISIBLE_DEVICES
          value: "0"
        - name: TOKENIZERS_PARALLELISM
          value: "false"
        - name: temperature
          value: "--kubetemperature--"
        - name: vectorsearchtype
          value: "--kubevectorsearchtype--"
        - name: contextwindowsize
          value: "--kubecontextwindowsize--"
        - name: vectordimension
          value: "--kubevectordimension--"
        - name: mainmodel
          value: "--kubemainmodel--"
        - name: mainembedding
          value: "--kubemainembedding--"
        - name: TSS
          value: "0"
        - name: KUBE
          value: "1"
        resources:             # REMOVE or COMMENT OUT: IF you DO NOT have NVIDIA GPU
          limits:              # REMOVE or COMMENT OUT: IF you DO NOT have NVIDIA GPU
            nvidia.com/gpu: 1  # REMOVE or COMMENT OUT: IF you DO NOT have NVIDIA GPU
        ports:
        - containerPort: 8001
      tolerations:             # REMOVE or COMMENT OUT: IF you DO NOT have NVIDIA GPU
      - key: nvidia.com/gpu    # REMOVE or COMMENT OUT: IF you DO NOT have NVIDIA GPU
        operator: Exists       # REMOVE or COMMENT OUT: IF you DO NOT have NVIDIA GPU
        effect: NoSchedule     # REMOVE or COMMENT OUT: IF you DO NOT have NVIDIA GPU
---
apiVersion: v1
kind: Service
metadata:
  name: privategpt-service
  labels:
    app: privategpt-service
spec:
  type: NodePort #Exposes the service as a node ports
  ports:
  - port: 8001
    name: p1
    protocol: TCP
    targetPort: 8001
  selector:
    app: privategpt
"""

  file_name=f"{op}/privategpt.yml"
  with open(file_name, "w") as file:
    file.write(ing)

  ing="""
################# ollama.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ollama
spec:
  selector:
    matchLabels:
      app: ollama
  replicas: 1 # tells deployment to run 1 pods matching the template
  template:
    metadata:
      labels:
        app: ollama
    spec:
      containers:
      - name: ollama
        image: --ollamacontainername-- # IF you DO NOT have NVIDIA GPU then CPU will be used
        imagePullPolicy: IfNotPresent  # You can also use Always, Never
        env:
        - name: NVIDIA_VISIBLE_DEVICES
          value: all
        - name: DP_DISABLE_HEALTHCHECKS
          value: xids
        - name: WEB_CONCURRENCY
          value: "--agenticai-kubeconcur--"
        - name: GPU
          value: "1"
        - name: COLLECTION
          value: "--agenticai-kubecollection--"
        - name: PORT
          value: "11434"
        - name: CUDA_VISIBLE_DEVICES
          value: "0"
        - name: TOKENIZERS_PARALLELISM
          value: "false"
        - name: temperature
          value: "--agenticai-kubetemperature--"
        - name: rollbackoffset
          value: "--agenticai-rollbackoffset--"
        - name: ollama-model
          value: "--agenticai-ollama-model--"
        - name: deletevectordbcount
          value: "--agenticai-deletevectordbcount--"
        - name: vectordbpath
          value: "--agenticai-vectordbpath--"
        - name: topicid
          value: "--agenticai-topicid--"
        - name: enabletls
          value: "--agenticai-enabletls--"
        - name: partition
          value: "--agenticai-partition--"
        - name: vectordbcollectionname
          value: "--agenticai-vectordbcollectionname--"
        - name: ollamacontainername
          value: "--agenticai-ollamacontainername--"
        - name: mainip
          value: "--agenticai-mainip--"
        - name: mainport
          value: "--agenticai-mainport--"
        - name: embedding
          value: "--agenticai-embedding--"
        - name: agents_topic_prompt
          value: "--agenticai-agents_topic_prompt--"
        - name: teamlead_topic
          value: "--agenticai-teamlead_topic--"
        - name: teamleadprompt
          value: "--agenticai-teamleadprompt--"
        - name: supervisor_topic
          value: "--agenticai-supervisor_topic--"
        - name: supervisorprompt
          value: "--agenticai-supervisorprompt--"
        - name: agenttoolfunctions
          value: "--agenticai-agenttoolfunctions--"
        - name: agent_team_supervisor_topic
          value: "--agenticai-agent_team_supervisor_topic--"
        - name: contextwindow
          value: "--agenticai-contextwindow--"          
        - name: TSS
          value: "0"
        - name: KUBE
          value: "1"
        resources:             # REMOVE or COMMENT OUT: IF you DO NOT have NVIDIA GPU
          limits:              # REMOVE or COMMENT OUT: IF you DO NOT have NVIDIA GPU
            nvidia.com/gpu: 1  # REMOVE or COMMENT OUT: IF you DO NOT have NVIDIA GPU
        ports:
        - containerPort: 11434
      tolerations:             # REMOVE or COMMENT OUT: IF you DO NOT have NVIDIA GPU
      - key: nvidia.com/gpu    # REMOVE or COMMENT OUT: IF you DO NOT have NVIDIA GPU
        operator: Exists       # REMOVE or COMMENT OUT: IF you DO NOT have NVIDIA GPU
        effect: NoSchedule     # REMOVE or COMMENT OUT: IF you DO NOT have NVIDIA GPU
---
apiVersion: v1
kind: Service
metadata:
  name: ollama-service
  labels:
    app: ollama-service
spec:
  type: NodePort #Exposes the service as a node ports
  ports:
  - port: 11434
    name: p1
    protocol: TCP
    targetPort: 11434
  selector:
    app: ollama
"""

  file_name=f"{op}/ollama.yml"
  with open(file_name, "w") as file:
    file.write(ing)

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
                step4cpatternscorethreshold='',step4clocalsearchtermfolder='',step4clocalsearchtermfolderinterval='',step4crtmsfoldername='',
                step3localfileinputfile='',step3localfiledocfolder='',step4crtmsmaxwindows='',step9contextwindowsize='',
                step9pgptcontainername='',step9pgpthost='',step9pgptport='',step9vectordimension='',
                step2raw_data_topic='',step2preprocess_data_topic='',step4raw_data_topic='',step4preprocesstypes='',
                step4jsoncriteria='',step4ajsoncriteria='',step4amaxrows='',step4apreprocesstypes='',step4araw_data_topic='',
                step4apreprocess_data_topic='',step4bpreprocesstypes='',step4bjsoncriteria='',step4braw_data_topic='',
                step4bpreprocess_data_topic='',step4preprocess_data_topic='',
                step9brollbackoffset='',
                step9bdeletevectordbcount='',
                step9bvectordbpath='',
                step9btemperature='',
                step9bvectordbcollectionname='',
                step9bollamacontainername='',
                step9bCUDA_VISIBLE_DEVICES='',
                step9bmainip='',
                step9bmainport='',
                step9bembedding='',
                step9bagents_topic_prompt='',
                step9bteamlead_topic='',
                step9bteamleadprompt='',
                step9bsupervisor_topic='',
                step9bagenttoolfunctions='',
                step9bagent_team_supervisor_topic='',step9bcontextwindow='',step9blocalmodelsfolder='',step9bagenttopic=''):
               
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
             - name: rawdata
               mountPath: /rawdata  # container folder where the local folder will be mounted
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
             - name: step3localfileinputfile # STEP 3 localfile inputfile field can be adjusted here.
               value: '{}'
             - name: step3localfiledocfolder # STEP 3 # STEP 3 docfolder inputfile field can be adjusted here.
               value: '{}'
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
             - name: step4crtmsmaxwindows # STEP 4c adjust RTMSMAXWINDOWS for Step 4c
               value: '{}'                           
             - name: step2raw_data_topic # STEP 2 
               value: '{}'                           
             - name: step2preprocess_data_topic # STEP 2 
               value: '{}'                           
             - name: step4raw_data_topic # STEP 4
               value: '{}'                           
             - name: step4preprocess_data_topic # STEP 4
               value: '{}'                                          
             - name: step4preprocesstypes # STEP 4
               value: '{}'                                          
             - name: step4jsoncriteria # STEP 4
               value: '{}'                           
             - name: step4ajsoncriteria # STEP 4a 
               value: '{}'                           
             - name: step4amaxrows # STEP 4a
               value: '{}'                           
             - name: step4apreprocesstypes # STEP 4a
               value: '{}'                           
             - name: step4araw_data_topic # STEP 4a
               value: '{}'                           
             - name: step4apreprocess_data_topic # STEP 4a
               value: '{}'                           
             - name: step4bpreprocesstypes # STEP 4b
               value: '{}'                           
             - name: step4bjsoncriteria # STEP 4b
               value: '{}'                           
             - name: step4braw_data_topic # STEP 4b 
               value: '{}'                           
             - name: step4bpreprocess_data_topic # STEP 4b 
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
             - name: step9contextwindowsize # privateGPT for contextwindow size
               value: '{}'                    
             - name: step9pgptcontainername # privateGPT container name
               value: '{}'                    
             - name: step9pgpthost # privateGPT host ip i.e.: http://127.0.0.1
               value: '{}'                    
             - name: step9pgptport # privateGPT port i.e. 8001
               value: '{}'                                   
             - name: step9vectordimension # privateGPT vector dimension
               value: '{}'                    
             - name: step9brollbackoffset
               value: '{}'
             - name: step9bdeletevectordbcount
               value: '{}'
             - name: step9bvectordbpath
               value: '{}'
             - name: step9btemperature
               value: '{}'
             - name: step9bvectordbcollectionname
               value: '{}'
             - name: step9bollamacontainername
               value: '{}'
             - name: step9bCUDA_VISIBLE_DEVICES
               value: '{}'
             - name: step9bmainip
               value: '{}'
             - name: step9bmainport
               value: '{}'
             - name: step9bembedding
               value: '{}'
             - name: step9bagents_topic_prompt
               value: '{}'
             - name: step9bteamlead_topic
               value: '{}'
             - name: step9bteamleadprompt
               value: '{}'
             - name: step9bsupervisor_topic
               value: '{}'
             - name: step9bagenttoolfunctions
               value: '{}'
             - name: step9bagent_team_supervisor_topic
               value: '{}'               
             - name: step9bcontextwindow
               value: '{}'                              
             - name: step9bagenttopic
               value: '{}'                              
             - name: step9blocalmodelsfolder
               value: '{}'                              
             - name: step1solutiontitle # STEP 1 solutiontitle field can be adjusted here. 
               value: '{}'                              
             - name: step1description # STEP 1 description field can be adjusted here. 
               value: '{}'        
             - name: KUBEBROKERHOST
               value: '{}'         
             - name: KAFKABROKERHOST
               value: '{}'                              
           volumes: 
           - name: dockerpath
             hostPath:
               path: /var/run/docker.sock
           - name: rawdata
             hostPath:
               path: /mnt  # CHANGE AS NEEDED TO YOUR LOCAL FOLDER the paths will be specific to your environment
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
                           airflowport,step3localfileinputfile,step3localfiledocfolder,step4maxrows,step4bmaxrows,step4cmaxrows,step4crawdatatopic,step4csearchterms,step4crememberpastwindows,step4cpatternwindowthreshold,
                           step4crtmsscorethreshold,step4cattackscorethreshold,step4cpatternscorethreshold,step4crtmsstream,step4clocalsearchtermfolder,step4clocalsearchtermfolderinterval,step4crtmsfoldername,step4crtmsmaxwindows,
                           step2raw_data_topic,step2preprocess_data_topic,step4raw_data_topic,step4preprocess_data_topic,step4preprocesstypes,step4jsoncriteria,step4ajsoncriteria,
                           step4amaxrows,step4apreprocesstypes,step4araw_data_topic,step4apreprocess_data_topic,step4bpreprocesstypes,step4bjsoncriteria,
                           step4braw_data_topic,step4bpreprocess_data_topic,
                           step5rollbackoffsets,step5processlogic,step5independentvariables,step6maxrows,step9rollbackoffset,
                           step9prompt,step9context,step9keyattribute,step9keyprocesstype,step9hyperbatch,step9vectordbcollectionname,step9concurrency,cudavisibledevices,
                           step9docfolder,step9docfolderingestinterval,step9useidentifierinprompt,step9searchterms,step9streamall,step9temperature,step9vectorsearchtype,
                           step9contextwindowsize,step9pgptcontainername,step9pgpthost,step9pgptport,step9vectordimension,
                           step9brollbackoffset,step9bdeletevectordbcount,step9bvectordbpath,step9btemperature,
                           step9bvectordbcollectionname,step9bollamacontainername,step9bCUDA_VISIBLE_DEVICES,step9bmainip,
                           step9bmainport,step9bembedding,step9bagents_topic_prompt,step9bteamlead_topic,step9bteamleadprompt,
                           step9bsupervisor_topic,step9bagenttoolfunctions,step9bagent_team_supervisor_topic,step9bcontextwindow,step9bagenttopic,step9blocalmodelsfolder,
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
                     step4cpatternscorethreshold='',step4clocalsearchtermfolder='',step4clocalsearchtermfolderinterval='',step4crtmsfoldername='',
                     step3localfileinputfile='',step3localfiledocfolder='',step4crtmsmaxwindows='',step9contextwindowsize='',
                     step9pgptcontainername='',step9pgpthost='',step9pgptport='',step9vectordimension='',
                     step2raw_data_topic='',step2preprocess_data_topic='',step4raw_data_topic='',step4preprocesstypes='',
                     step4jsoncriteria='',step4ajsoncriteria='',step4amaxrows='',step4apreprocesstypes='',step4araw_data_topic='',
                     step4apreprocess_data_topic='',step4bpreprocesstypes='',step4bjsoncriteria='',step4braw_data_topic='',
                     step4bpreprocess_data_topic='',step4preprocess_data_topic='',
                     step9brollbackoffset='',
                     step9bdeletevectordbcount='',
                     step9bvectordbpath='',
                     step9btemperature='',
                     step9bvectordbcollectionname='',
                     step9bollamacontainername='',
                     step9bCUDA_VISIBLE_DEVICES='',
                     step9bmainip='',
                     step9bmainport='',
                     step9bembedding='',
                     step9bagents_topic_prompt='',
                     step9bteamlead_topic='',
                     step9bteamleadprompt='',
                     step9bsupervisor_topic='',
                     step9bagenttoolfunctions='',
                     step9bagent_team_supervisor_topic='',step9bcontextwindow='',step9blocalmodelsfolder='',step9bagenttopic=''):
                                         
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
             - name: rawdata
               mountPath: /rawdata   # container folder where the local folder will be mounted                           
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
             - name: step3localfileinputfile # STEP 3 localfile inputfile field can be adjusted here.
               value: '{}'
             - name: step3localfiledocfolder # STEP 3 # STEP 3 docfolder inputfile field can be adjusted here.
               value: '{}'               
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
             - name: step4crtmsmaxwindows # STEP 4c adjust RTMSMAXWINDOWS for Step 4c
               value: '{}'                                       
             - name: step2raw_data_topic # STEP 2 
               value: '{}'                           
             - name: step2preprocess_data_topic # STEP 2 
               value: '{}'                           
             - name: step4raw_data_topic # STEP 4
               value: '{}'                           
             - name: step4preprocess_data_topic # STEP 4
               value: '{}'                                                         
             - name: step4preprocesstypes # STEP 4
               value: '{}'                                                         
             - name: step4jsoncriteria # STEP 4
               value: '{}'                           
             - name: step4ajsoncriteria # STEP 4a 
               value: '{}'                           
             - name: step4amaxrows # STEP 4a
               value: '{}'                           
             - name: step4apreprocesstypes # STEP 4a
               value: '{}'                           
             - name: step4araw_data_topic # STEP 4a
               value: '{}'                           
             - name: step4apreprocess_data_topic # STEP 4a
               value: '{}'                           
             - name: step4bpreprocesstypes # STEP 4b
               value: '{}'                           
             - name: step4bjsoncriteria # STEP 4b
               value: '{}'                           
             - name: step4braw_data_topic # STEP 4b 
               value: '{}'                           
             - name: step4bpreprocess_data_topic # STEP 4b 
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
             - name: step9contextwindowsize # context window size
               value: '{}'                                                                                          
             - name: step9pgptcontainername # privateGPT container name
               value: '{}'                    
             - name: step9pgpthost # privateGPT host ip i.e.: http://127.0.0.1
               value: '{}'                    
             - name: step9pgptport # privateGPT port i.e. 8001
               value: '{}'                                                  
             - name: step9vectordimension # privateGPT vector dimension
               value: '{}'                                                                 
             - name: step9brollbackoffset
               value: '{}'
             - name: step9bdeletevectordbcount
               value: '{}'
             - name: step9bvectordbpath
               value: '{}'
             - name: step9btemperature
               value: '{}'
             - name: step9bvectordbcollectionname
               value: '{}'
             - name: step9bollamacontainername
               value: '{}'
             - name: step9bCUDA_VISIBLE_DEVICES
               value: '{}'
             - name: step9bmainip
               value: '{}'
             - name: step9bmainport
               value: '{}'
             - name: step9bembedding
               value: '{}'
             - name: step9bagents_topic_prompt
               value: '{}'
             - name: step9bteamlead_topic
               value: '{}'
             - name: step9bteamleadprompt
               value: '{}'
             - name: step9bsupervisor_topic
               value: '{}'
             - name: step9bagenttoolfunctions
               value: '{}'
             - name: step9bagent_team_supervisor_topic
               value: '{}'                              
             - name: step9bcontextwindow
               value: '{}'                                             
             - name: step9bagenttopic
               value: '{}'                              
             - name: step9blocalmodelsfolder
               value: '{}'                                             
             - name: step1solutiontitle # STEP 1 solutiontitle field can be adjusted here. 
               value: '{}'                              
             - name: step1description # STEP 1 description field can be adjusted here. 
               value: '{}'                                          
             - name: KUBEBROKERHOST
               value: '{}'         
             - name: KAFKABROKERHOST
               value: '{}'                              
           volumes: 
           - name: dockerpath
             hostPath:
               path: /var/run/docker.sock
           - name: rawdata
             hostPath:
               path: /mnt  # CHANGE AS NEEDED TO YOUR LOCAL FOLDER the paths will be specific to your environment
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
                           mqttuser,airflowport,step3localfileinputfile,step3localfiledocfolder,step4maxrows,step4bmaxrows,step4cmaxrows,step4crawdatatopic,step4csearchterms,step4crememberpastwindows,step4cpatternwindowthreshold,
                           step4crtmsscorethreshold,step4cattackscorethreshold,step4cpatternscorethreshold,step4crtmsstream,step4clocalsearchtermfolder,step4clocalsearchtermfolderinterval,step4crtmsfoldername,step4crtmsmaxwindows,
                           step2raw_data_topic,step2preprocess_data_topic,step4raw_data_topic,step4preprocess_data_topic,step4preprocesstypes,step4jsoncriteria,step4ajsoncriteria,
                           step4amaxrows,step4apreprocesstypes,step4araw_data_topic,step4apreprocess_data_topic,step4bpreprocesstypes,step4bjsoncriteria,
                           step4braw_data_topic,step4bpreprocess_data_topic,                           
                           step5rollbackoffsets,step5processlogic,step5independentvariables,step6maxrows,step9rollbackoffset,
                           step9prompt,step9context,step9keyattribute,step9keyprocesstype,step9hyperbatch,step9vectordbcollectionname,step9concurrency,cudavisibledevices,
                           step9docfolder,step9docfolderingestinterval,step9useidentifierinprompt,step9searchterms,step9streamall,step9temperature,step9vectorsearchtype,
                           step9contextwindowsize,step9pgptcontainername,step9pgpthost,step9pgptport,step9vectordimension,
                           step9brollbackoffset,step9bdeletevectordbcount,step9bvectordbpath,step9btemperature,
                           step9bvectordbcollectionname,step9bollamacontainername,step9bCUDA_VISIBLE_DEVICES,step9bmainip,
                           step9bmainport,step9bembedding,step9bagents_topic_prompt,step9bteamlead_topic,step9bteamleadprompt,
                           step9bsupervisor_topic,step9bagenttoolfunctions,step9bagent_team_supervisor_topic,step9bcontextwindow,step9bagenttopic,step9blocalmodelsfolder,                           
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

def optimizecontainer2(cname, sname, sd):
    rbuf = os.environ.get('READTHEDOCS', '')
    
    # 1. Cleanly build parameters to skip heavy inline shell interpolation strings
    env_vars = {
        'GPG_KEY': '', 'PYTHON_SHA256': '', 'TSS': '-9',
        'MQTTPASSWORD': '', 'DOCKERPASSWORD': '', 'SMTP_PASSWORD': '',
        'SMTP_SERVER': '', 'SMTP_USERNAME': '', 'GITPASSWORD': '',
        'recipient': '', 'PATH': '', 'KAFKACLOUDPASSWORD': '',
        'DOCKERUSERNAME': os.environ.get('DOCKERUSERNAME', ''),
        'SOLUTIONNAME': str(sname),
        'SOLUTIONDAG': str(sd),
        'READTHEDOCS': rbuf[:4]
    }
    
    # Build env array arguments for the docker execution line safely
    env_args = []
    for k, v in env_vars.items():
        env_args.extend(["--env", f"{k}={v}"])

    # Construct complete command list to avoid using slow `shell=True` for container creation
    cmd = ["docker", "run", "-d", "-v", "/var/run/docker.sock:/var/run/docker.sock:z"] + env_args + [cname]
    
    print(f"Container optimizing: {' '.join(cmd)[:200]}...") 
    
    try:
        # Capture the spawned Container ID directly to track it perfectly
        container_id = subprocess.check_output(cmd).decode("utf-8").strip()
    except Exception as e:
        print("ERROR launching container: ", e)
        return "failed"

    print(f"Tracking Container ID: {container_id[:12]}")

    status = ""
    start_time = time.time()
    timeout = 450  # 90 iterations * 5s equivalent max ceiling

    # 2. Adaptive Backoff Loop: Start fast, scale out if the 17GB processing takes longer
    poll_interval = 1.0 
    
    while True:
        elapsed = time.time() - start_time
        if elapsed > timeout:
            print("WARN: Unable to optimize container (Timeout reached)")
            break
            
        try:
            # 🟢 THE SPEED FIX: Use precise container status targeting.
            # 'docker inspect' returns a clean state code rather than parsing huge string blocks.
            check_cmd = ["docker", "inspect", "-f", "{{.State.Running}}", container_id]
            is_running = subprocess.check_output(check_cmd).decode("utf-8").strip()
            
            if is_running == "false":
                print("INFO: Container optimized and finished execution.")  
                status = "good"
                break
                
        except subprocess.CalledProcessError:
            # Container was auto-removed or disappeared when finished, indicating completion
            print("INFO: Container optimized (Lifecycle Complete)")
            status = "good"
            break
        except Exception as e:
            print("ERROR while tracking container state: ", e)
            
        # Dynamically scale intervals up to 4s max cap if processing is heavy
        time.sleep(poll_interval)
        if poll_interval < 4.0:
            poll_interval += 0.5

    # 3. Handle post-optimization verification tasks
    if status == "good":
        # Combine image tag operations or keep them standard without shell dependencies
        subprocess.call(["docker", "image", "tag", f"{cname}sq:latest", cname], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.call(["docker", "rmi", f"{cname}sq:latest", "--force"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        print(f"🚀 Optimization verified. Initiating async push for {cname}...")
        
        # 🟢 THE BULK FLATTEN PUSH FIX: Cap network/disk allocation threads 
        # Limits multi-core worker memory footprints from spiking on huge structural pushes
        push_env = os.environ.copy()
        push_env["GOMAXPROCS"] = "1"
        
        subprocess.Popen(
            f"docker push {cname}", 
            shell=True,
            env=push_env,
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.DEVNULL
        )
        
        # Fast garbage collection 
        subprocess.Popen("docker image prune -f", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)    

    return status
    
def optimizecontainer(cname,sname,sd):
    rbuf=os.environ['READTHEDOCS']
    buf="docker run -d -v /var/run/docker.sock:/var/run/docker.sock:z --env GPG_KEY='' --env PYTHON_SHA256='' --env DOCKERUSERNAME='{}' --env SOLUTIONNAME={} --env SOLUTIONDAG={} --env TSS=-9  --env READTHEDOCS='{}' --env MQTTPASSWORD='' --env DOCKERPASSWORD='' --env SMTP_PASSWORD='' --env SMTP_SERVER='' --env SMTP_USERNAME='' --env  GITPASSWORD='' --env recipient='' --env PATH='' --env KAFKACLOUDPASSWORD='' {}".format(os.environ['DOCKERUSERNAME'], sname, sd, rbuf[:4],cname )
    
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


      if status == "good":
        # 1. Update the image metadata tags
        buf = "docker image tag {}sq:latest {}".format(cname, cname)
        print("Docker image tag: {}".format(buf))
        subprocess.call(buf, shell=True)
        
        # 2. Remove the temporary 'sq' image pointer 
        buf = "docker rmi {}sq:latest --force".format(cname)
        print("Docker image rmi: {}".format(buf))
        subprocess.call(buf, shell=True)
        
        # 3. Trigger the background push safely
        print("🚀 Optimization verified. Initiating async push for {}...".format(cname))
        proc = subprocess.Popen(
            "docker push {}".format(cname), 
            shell=True,
            stdout=subprocess.DEVNULL,  # Prevents 17GB of progress bars from flooding your logs
            stderr=subprocess.DEVNULL
        )
        
        # 4. Clean up dangling builder layers AFTER the push process is handed off to the engine daemon
        subprocess.call("docker image prune -f", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)    

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

def loadmitre(fname):
    d=""
    try:
      with open(fname) as f:
        d = json.load(f)
        return d
    except Exception as e:
       print("Error reading file {} {}".format(fname,e)) 
       return "" 

def getmitre(mess,fname):

    tactic=""
    technique=""
    tacticarr=[]
    techniquearr=[]
    
    dj=loadmitre(fname)
    if dj=="":
        return "na","na",""
    
    for key, values in dj.items():
         #print(f"{key}{values}")
         if key in mess:
             key=key.replace(" ","_")
             tacticarr.append(key)
             for v in values:
               if v in mess:
                 v=v.replace(" ","_")  
                 techniquearr.append(v)
    if len(tacticarr)>0 and len(techniquearr)>0:
           tacticarr=set(tacticarr)
           techniquearr=set(techniquearr)        
           tactic='-'.join(tacticarr)
           technique='-'.join(techniquearr)
           jb=",\"tactic\":\""+tactic+"\",\"technique\":\""+technique+"\""
           return tactic, technique,jb

    if len(tacticarr)==0: # may be only technique is given - then find associated tactic
       for key, values in dj.items():
             key=key.replace(" ","_")             
             for v in values:
               if v in mess:
                 v=v.replace(" ","_")  
                 techniquearr.append(v)  
                 tacticarr.append(key)  
       if len(tacticarr)>0 and len(techniquearr)>0:
           tacticarr=set(tacticarr)
           techniquearr=set(techniquearr)
           tactic='-'.join(tacticarr)
           technique='-'.join(techniquearr)
           jb=",\"tactic\":\""+tactic+"\",\"technique\":\""+technique+"\""
           return tactic, technique,jb
    
    return "na","na",""

def dorst2pdf(spath,opath):

    rst_files = ["details.rst",  "operating.rst",  "usage.rst", "kube.rst",  "logs.rst"]
    pdf_files = []
    directory_path = f"{opath}/pdf_documentation/"

    os.makedirs(directory_path, exist_ok=True) 

    for rst_file in rst_files:
        rst_filef=f"{spath}/{rst_file}"
        pdf_file = rst_file.replace('.rst', '.pdf')        
        pdf_filef=f"{opath}/pdf_documentation/{pdf_file}"

        print("pdffile=",pdf_filef,rst_filef)
        subprocess.call("rst2pdf {} -o {}".format(rst_filef,pdf_filef), shell=True)

        pdf_files.append(pdf_filef)

    return pdf_files,directory_path

def mergepdf(opath,pdffiles,sname):
      try:
        merger = PdfWriter()

        for pdf in pdffiles:
            merger.append(pdf)
        wpath=f"{opath}/{sname}.pdf"
        print("wpath=",wpath)
        merger.write(wpath)
        merger.close()

        for pdf in pdffiles:
            os.remove(pdf)
      except Exception as e:
        pass

############################################# LOG Entity

class UniversalThreatAgent:
    def __init__(self, patterns_config_path: str, mitre_json_path: str, weights_profile_path: str, baseline_state_path: str = "/rawdata/rtmsbaseline.txt"):
        self.compiled_rules = {}
        self.file_registry: Dict[str, int] = {}
        self.active_locks: Dict[str, Any] = {}
        
        self.baseline_state_path = baseline_state_path
        self.baseline_cache: Dict[str, float] = {}
        self.last_baseline_time: datetime.datetime = None
        
        self.executor = ThreadPoolExecutor(max_workers=4)

        # 1. Load the external threat weights profile configuration
        if not os.path.exists(weights_profile_path):
            print(f"[CRITICAL ERROR] Threat weights profile configuration file missing: {weights_profile_path}", file=sys.stderr)
            sys.exit(1)
            
        with open(weights_profile_path, 'r', encoding='utf-8') as f:
            profile = json.load(f)
            self.complexity_map = profile.get("attack_complexity_weights", {})
            self.vulnerability_map = profile.get("entity_vulnerability_weights", {})
            self.fallbacks = profile.get("fallbacks", {})

        # 2. Load persistent baseline storage history from disk if available to avoid PSI resets
        baseline_dir = os.path.dirname(self.baseline_state_path)
        if baseline_dir and not os.path.exists(baseline_dir):
            try:
                os.makedirs(baseline_dir, exist_ok=True)
            except Exception as e:
                print(f"[WARN] Failed to pre-create directory structure {baseline_dir}: {e}", file=sys.stderr)

        if os.path.exists(self.baseline_state_path):
            try:
                with open(self.baseline_state_path, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                    self.baseline_cache = state.get("cache", {})
                    if state.get("last_baseline_time"):
                        self.last_baseline_time = datetime.datetime.fromisoformat(state["last_baseline_time"])
                print(f"[INIT] Successfully loaded persistent baseline historical profiles from {self.baseline_state_path}", file=sys.stderr)
            except Exception as e:
                print(f"[WARN] Persistent baseline state could not be loaded from {self.baseline_state_path}, initializing cold start: {e}", file=sys.stderr)

        # 3. Load and validate core framework matrix
        if not os.path.exists(mitre_json_path):
            print(f"[CRITICAL ERROR] Core mitre.json framework matrix file missing: {mitre_json_path}", file=sys.stderr)
            sys.exit(1)
            
        with open(mitre_json_path, 'r', encoding='utf-8') as f:
            self.mitre_matrix = json.load(f)
            
        # 4. Compile rule configurations from JSON map
        if os.path.exists(patterns_config_path):
            with open(patterns_config_path, 'r', encoding='utf-8') as f:
                rules_data = json.load(f)
                for alert_name, meta in rules_data.items():
                    tactic = meta.get("mitre_tactic")
                    technique = meta.get("mitre_technique")
                    is_validated = (tactic in self.mitre_matrix and technique in self.mitre_matrix[tactic])
                    
                    self.compiled_rules[alert_name] = {
                        "regex": re.compile(meta["pattern"]),
                        "mitre_tactic": tactic,
                        "mitre_technique": technique,
                        "validated_by_matrix": is_validated
                    }

    def _get_formatted_date(self) -> str:
        return datetime.datetime.now(timezone.utc).strftime("%Y.%m.%d")

    def _calculate_dynamic_pattern_score(self, tactic: str, technique: str, entity: str) -> float:
        tactic_lower = tactic.lower()
        technique_lower = technique.lower()
        entity_lower = str(entity).lower()

        a_w = self.fallbacks.get("default_a_w", 5.0)
        for keyword, weight in self.complexity_map.items():
            if keyword in tactic_lower or keyword in technique_lower:
                a_w = weight
                break 

        e_w = None
        for keyword, weight in self.vulnerability_map.items():
            if keyword in entity_lower:
                e_w = weight
                break

        if e_w is None:
            ip_pattern = re.compile(r'\b\d{1,3}(?:\.\d{1,3}){3}\b')
            if ip_pattern.search(entity):
                e_w = self.fallbacks.get("network_ip_e_w", 7.5)
            else:
                e_w = self.fallbacks.get("default_e_w", 4.5)

        dynamic_score = math.sqrt(a_w * e_w) * 10.0
        return round(dynamic_score, 2)

    def _build_element(self, file_path: str, line_num: int, event_type: str, entity: str, mitre_meta: Dict[str, Any], attributes: Dict[str, Any]) -> Dict[str, Any]:
        element = {
            "date": self._get_formatted_date(),
            "datetime": datetime.datetime.now(timezone.utc).isoformat(),
            "log_file": os.path.abspath(file_path),
            "line_number": line_num,
            "event_type": event_type,
            "entity": str(entity) if entity else "unknown_entity",
            "mitre_classification": mitre_meta
        }
        attr_idx = 1
        for k, v in attributes.items():
            if k != "entity" and k != "entity_alt" and v is not None:
                element[f"attr{attr_idx}"] = str(v)
                attr_idx += 1
        return element

    def extract_from_json(self, record: Dict[str, Any], file_path: str, line_num: int) -> Dict[str, Any]:
        keys = list(record.keys())
        entity_fallbacks = ["src_ip", "client_ip", "source_ip", "username", "user", "process_path", "image", "resource_arn", "device_id", "hostname"]
        entity_key = next((anchor for anchor in entity_fallbacks if anchor in keys), keys[0] if keys else "unclassified")
        
        mitre_meta = {
            "tactic": "Initial Access", 
            "technique": "Valid Accounts", 
            "validated_by_matrix": False
        }
        
        extracted_entity = record.get(entity_key, "unclassified")
        return self._build_element(file_path, line_num, "native_structured_telemetry", extracted_entity, mitre_meta, record)

    def parse_fallback_text(self, line: str, file_path: str, line_num: int) -> Dict[str, Any]:
        tokens = line.split()
        entity = None
        entity_category = "unclassified"
        
        # 1. Advanced Threat Extraction Patterns
        ip_pattern = re.compile(r'\b\d{1,3}(?:\.\d{1,3}){3}\b')
        ipv6_pattern = re.compile(r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b')
        
        # Filesystem paths, configuration records, binary files, and extensions
        filesystem_pattern = re.compile(
            r'(?:[a-zA-Z]:\\(?:[^\\\s<>:"/|?*]+\\)*[^\\\s<>:"/|?*]+|'  # Windows
            r'/(?:bin|etc|var|usr|opt|tmp|root|home|sys|proc|lib|run|mnt)/[^\s<>:"|?*]+|' # Linux standard trees
            r'\b[a-zA-Z0-9_\-.]+\.(?:exe|dll|bat|sh|ps1|vbs|py|elf|bin|conf|ini|cfg|log|zip|tar|gz)\b)', # Security sensitive extensions
            re.IGNORECASE
        )
        
        # Network infrastructure indicators (URLs, Domains, Internal Appliances)
        url_domain_pattern = re.compile(r'\b(?:https?://)?(?:[a-zA-Z0-9\-]+\.)+[a-zA-Z]{2,}(?::\d+)?(?:/[^\s]*)?\b')
        router_pattern = re.compile(r'\b(Router|Switch|Firewall|Core-SW|Edge|Gateway|LoadBalancer)-\S+\b', re.IGNORECASE)
        
        # --- Sequential Extraction Cascade Execution ---
        for token in tokens:
            clean_token = token.strip(":,[]()\"'-_")
            if not clean_token:
                continue

            # Level A: IP Network Indicators
            if ip_pattern.search(clean_token):
                entity = ip_pattern.search(clean_token).group(0)
                entity_category = "network_ip"
                break
            elif ipv6_pattern.search(clean_token):
                entity = ipv6_pattern.search(clean_token).group(0)
                entity_category = "network_ip_v6"
                break

            # Level B: Filesystem and System Targets
            elif filesystem_pattern.search(clean_token):
                entity = clean_token
                entity_category = "filesystem_resource"
                break

            # Level C: Network Identifiers and Infrastructure Devices
            elif url_domain_pattern.search(clean_token):
                entity = clean_token
                entity_category = "network_endpoint_domain"
                break
            elif router_pattern.match(clean_token):
                entity = clean_token
                entity_category = "network_appliance"
                break

        # Level D: High-Risk Attack Target Accounts (Fallback bucket)
        if not entity:
            for token in tokens:
                clean_token = token.strip(":,[]()\"'-_")
                if clean_token.lower() in ['root', 'administrator', 'trustedinstaller', 'sshd', 'kubelet', 'system']:
                    entity = clean_token
                    entity_category = "privileged_system_context"
                    break

        # If nothing of threat significance is isolated, return an empty object to drop the telemetry slice
        if not entity:
            return {}

        # Dynamically escalate context metadata mapping based on isolated vectors
        mitre_meta = {
            "tactic": "Defense Evasion" if entity_category == "filesystem_resource" else "Discovery", 
            "technique": f"Targeted Resource Asset Isolation ({entity_category})", 
            "validated_by_matrix": False
        }
        
        attrs = {f"token_{i}": tok for i, tok in enumerate(tokens, start=1) if i <= 8}
        attrs["extracted_entity_category"] = entity_category
        
        return self._build_element(file_path, line_num, f"threat_vector_{entity_category}", entity, mitre_meta, attrs)
    
    def parse_line_to_object(self, raw_line: str, file_path: str, line_num: int) -> Dict[str, Any]:
        cleaned = raw_line.strip()
        if not cleaned: 
            return {}

        if cleaned.startswith('{') and cleaned.endswith('}'):
            try: 
                return self.extract_from_json(json.loads(cleaned), file_path, line_num)
            except json.JSONDecodeError: 
                pass

        for alert_name, rule in self.compiled_rules.items():
            match = rule["regex"].search(cleaned)
            if match:
                if alert_name == "windows_cbs_generic_stream":
                    return {}
                
                match_dict = match.groupdict()
                extracted_entity = match_dict.get("entity") or match_dict.get("entity_alt")
                
                mitre_meta = {
                    "tactic": rule["mitre_tactic"],
                    "technique": rule["mitre_technique"],
                    "validated_by_matrix": rule["validated_by_matrix"]
                }
                return self._build_element(file_path, line_num, alert_name, extracted_entity, mitre_meta, match_dict)

        return self.parse_fallback_text(cleaned, file_path, line_num)
    
    def scan_file_incremental(self, file_path: str) -> List[Dict[str, Any]]:
        elements_collected = []
        last_position = self.file_registry.get(file_path, 0)
        
        # 1. Instantiating here locks deduplication to ONLY this file session instance
        seen_entities_per_file = set()
        
        try: 
            current_size = os.path.getsize(file_path)
        except FileNotFoundError: 
            return []
            
        if current_size < last_position: 
            last_position = 0
        if current_size == last_position: 
            return [] 
            
        f = None
        try:
            f = open(file_path, 'r', encoding='utf-8', errors='ignore')
            fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            
            line_count = 1
            if last_position > 0:
                f.seek(0)
                for line in f:
                    if f.tell() > last_position:
                        break
                    line_count += 1
            else:
                f.seek(0)
            
            for line in f:
                parsed_element = self.parse_line_to_object(line, file_path, line_count)
                if parsed_element:
                    entity = parsed_element.get("entity")
                    
                    # 2. Check and enforce uniqueness per file boundary
                    if entity and entity not in seen_entities_per_file:
                        seen_entities_per_file.add(entity)
                        elements_collected.append(parsed_element)
                        
                line_count += 1
                
            self.file_registry[file_path] = f.tell()
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            f.close()
            
        except (IOError, OSError):
            if f: f.close()
            return []
        except Exception as e:
            print(f"[ERROR] Disk operations exception on {file_path}: {str(e)}", file=sys.stderr)
            if f:
                try: f.close()
                except: pass
        return elements_collected
    
    def stream_chunk_to_kafka(self, chunk_data: list, topic: str, host: str, port: str, token: str, args: Dict):
        for element in chunk_data:
            try:
                payload = json.dumps(element)
                # Production Producer implementation logic wraps directly here
                topicid = int(args.get('topicid', 0))
                delay = int(args.get('delay', 0))
                enabletls = int(args.get('enabletls', 0))
                identifier = args.get('identifier', '')
                try:
                    result=maadstml.viperproducetotopic(token,host,port,topic,"rtms-stream",enabletls,delay,'','', '',0,payload,"",
                                                        topicid,identifier)
                except Exception as e:
                    print("ERROR:",e)
     
            except Exception as e:
                print(f"[THREAD ERROR] Failed to produce record: {str(e)}", file=sys.stderr)


    def calculate_baseline(self, log_data: List[Dict[str, Any]], update_interval_hours: int, field_name: str = "event_type") -> Dict[str, float]:
        """ Calculates structural baseline drifting profiles securely against division by zero """
        now = datetime.datetime.now(datetime.timezone.utc)
        current_values = [item[field_name] for item in log_data if field_name in item]
        total_count = len(current_values)
        
        if total_count == 0:
            return self.baseline_cache
            
        current_counts = Counter(current_values)
        actual_dist = {key: round(count / total_count, 4) for key, count in current_counts.items()}
        
        category_psi_lookup = {}
        # Calculate live metric variation if reference profiles are active
        if self.baseline_cache:
            all_categories = set(self.baseline_cache.keys()).union(set(actual_dist.keys()))
            for category in all_categories:
                # Use max() to securely prevent zero denominators if 0 or 0.0 is explicitly saved in the file
                b = max(float(self.baseline_cache.get(category, 0.0001)), 0.0001)
                a = max(float(actual_dist.get(category, 0.0001)), 0.0001)
                
                # Safe from zero-division and log(0) domain issues
                category_psi = (a - b) * math.log(a / b)
                category_psi_lookup[category] = round(category_psi, 4)
        else:
            # Initial cold start fallback metric value
            category_psi_lookup = {cat: 0.2979 for cat in actual_dist.keys()}

        for item in log_data:
            if field_name in item:
                item_type = item.get(field_name)
                item["event_type_PSI"] = category_psi_lookup.get(item_type, 0.2979)

        # Handle chronological time windows and write tracking state directly to disk
        should_update_cache = (self.last_baseline_time is None)
        if self.last_baseline_time:
            hours_elapsed = (now - self.last_baseline_time).total_seconds() / 3600
            if hours_elapsed >= update_interval_hours:
                should_update_cache = True
                
        if should_update_cache:
            self.last_baseline_time = now
            self.baseline_cache = dict(sorted(actual_dist.items(), key=lambda x: x[1], reverse=True))
            
            try:
                state_payload = {
                    "last_baseline_time": self.last_baseline_time.isoformat(),
                    "cache": self.baseline_cache
                }
                with open(self.baseline_state_path, 'w', encoding='utf-8') as f:
                    json.dump(state_payload, f, indent=2)
            except Exception as e:
                print(f"[ERROR] Failed writing persistent tracking state out to {self.baseline_state_path}: {e}", file=sys.stderr)
            
        return self.baseline_cache
              

    def parallel_stream_to_kafka(self, global_elements: list, topic: str, host: str, port: str, token: str, args: Dict, num_threads: int = 4):
        total_elements = len(global_elements)
        if total_elements == 0:
            return
        chunk_size = math.ceil(total_elements / num_threads)
        
        # USE THE PERSISTENT EXECUTOR: No 'with' block, no automatic shutdown
        futures = []
        for i in range(num_threads):
            start_idx = i * chunk_size
            end_idx = min(start_idx + chunk_size, total_elements)
            chunk = global_elements[start_idx:end_idx]
            if not chunk: continue
            
            # Submit to the long-lived pool
            #future = self.executor.submit(self.stream_chunk_to_kafka, chunk, topic, host, port, token, args)
#            futures.append(future)

            try:
                # Try using the executor first
                future = self.executor.submit(self.stream_chunk_to_kafka, chunk, topic, host, port, token, args)
                futures.append(future)
            except RuntimeError as e:
                if "shutdown" in str(e).lower():
                    # WORKAROUND: If the executor is shutting down, execute it synchronously right here!
                    print("[WARN] Executor is shutting down. Falling back to synchronous streaming.", file=sys.stderr)
                    self.stream_chunk_to_kafka(chunk, topic, host, port, token, args)
                else:
                    raise e
            
        # Wait for the current batch to finish
        for future in futures:
            future.result()


    def watch_directories(self, folders: List[str], interval_seconds: int, update_interval_hours: int, topic: str, host: str, port: str, token: str, args: Dict):
        print(f"[STARTUP] Multi-Entity Agent Monitoring {len(folders)} paths every {interval_seconds}s.", file=sys.stderr)
        try:
            while True:
                global_interval_elements = []
                for target_folder in folders:
                    if not os.path.exists(target_folder): 
                        continue
                    try:
                        entries = sorted(
                            [e for e in os.scandir(target_folder) if e.is_file()],
                            key=lambda x: x.name
                        )
                    except Exception:
                        continue

                    for entry in entries:
                        file_elements = self.scan_file_incremental(entry.path)
                        if file_elements:
                            global_interval_elements.extend(file_elements)
                
                if global_interval_elements:                
                    self.calculate_baseline(global_interval_elements, update_interval_hours, "event_type")
                    
                    raw_scores = []
                    for item in global_interval_elements:
                        mitre = item.get("mitre_classification", {})
                        tactic = mitre.get("tactic", "Unclassified Context")
                        technique = mitre.get("technique", "Unknown")
                        entity = item.get("entity", "unknown_entity")
                        
                        pattern_score = self._calculate_dynamic_pattern_score(tactic, technique, entity)
                        item["pattern_score"] = pattern_score
                        
                        psi_drift = float(item.get("event_type_PSI", 0.2979))
                        final_raw = pattern_score * math.exp(psi_drift)
                        item["raw_rtms_score"] = round(final_raw, 2)
                        raw_scores.append(final_raw)
                        
                    n = len(raw_scores)
                    mu = sum(raw_scores) / n if n > 0 else 0.0
                    variance = sum((x - mu) ** 2 for x in raw_scores) / n if n > 0 else 0.0
                    sigma = math.sqrt(variance)
                    
                    for item in global_interval_elements:
                        raw_rtms = item["raw_rtms_score"]
                        if sigma == 0:
                            item["normalized_rtms_score"] = 50.0
                        else:
                            z_score = (raw_rtms - mu) / sigma
                            try:
                                normalized_score = 100.0 / (1.0 + math.exp(-z_score))
                            except OverflowError:
                                normalized_score = 100.0 if z_score > 0 else 0.0
                            item["normalized_rtms_score"] = round(normalized_score, 2)

                    print(json.dumps(global_interval_elements, indent=2), flush=True)
                    
                    self.parallel_stream_to_kafka(
                        global_elements=global_interval_elements,
                        topic=topic, host=host, port=port, token=token, args=args, num_threads=4
                    )

                time.sleep(interval_seconds)
        except KeyboardInterrupt:
            print("\n[SHUTDOWN] Exiting monitoring loop.", file=sys.stderr)

def extractLogEntities(CONFIG_RULES, MITRE_MATRIX, WEIGHTS_PROFILE, user_folders_raw, user_interval, update_interval_hours, KAFKA_TOPIC, KAFKA_HOST, KAFKA_PORT, VIPERTOKEN, args):
   try:
    agent = UniversalThreatAgent(
        patterns_config_path=CONFIG_RULES, 
        mitre_json_path=MITRE_MATRIX, 
        weights_profile_path=WEIGHTS_PROFILE,
        baseline_state_path="/rawdata/rtmsbaseline.txt"
    )
    userfolders = user_folders_raw.split(",")
    agent.watch_directories(
        folders=userfolders, 
        interval_seconds=user_interval, 
        update_interval_hours=int(update_interval_hours), 
        topic=KAFKA_TOPIC, host=KAFKA_HOST, port=KAFKA_PORT, token=VIPERTOKEN, args=args
    )
   except Exception:
    print("--- FATAL ERROR TRACEBACK ---")
    traceback.print_exc()
    sys.exit(1)

    
    #if __name__ == "__main__":
#    CONFIG_RULES = "mitre-security-mapping.json"
#    MITRE_MATRIX = "mitre.json"
#    user_folders_raw = "/mnt/c/maads/tml-airflow/rawdata/mylogs"
#    target_folders = [f.strip() for f in user_folders_raw.split(",") if f.strip()]
#    try: user_interval = 4
#    except ValueError: user_interval = 5
#    if not target_folders: sys.exit(1)
#    agent = UniversalThreatAgent(patterns_config_path=CONFIG_RULES, mitre_json_path=MITRE_MATRIX)
#    agent.watch_directories(folders=target_folders, interval_seconds=user_interval)
