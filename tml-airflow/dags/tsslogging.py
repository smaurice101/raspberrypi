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
