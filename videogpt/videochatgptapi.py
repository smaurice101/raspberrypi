import maadstml
import os
import time

def analysevideos(filename,prompt,responsefolder):
    url="http://127.0.0.1"
    port="7800"

    # The response from VideoGPT is stored in this .TXT file for the video
    fname="c:/maads/privategpt/Video_ChatGPT/video_chatgpt/demo/demo_sample_videos/" + filename + ".txt"
    
    try:
        # remove old response if exists
        os.remove(fname)
    except Exception as e:
       pass  
    response=maadstml.videochatloadresponse(url,port,filename,prompt,responsefolder,temperature=0.2,max_output_tokens=512)
    # try to wait for file to exist
    while not os.path.isfile(fname):
      continue

    # Here is the Video GPT response
    time.sleep(2)
    try:
      #print("fname=",fname)  
      with open(fname,"r") as f:
         print("File contents=",f.read())
    except Exception as e:
      print(e)  

      
# put videos here:
#/mnt/c/maads/privategpt/Video_ChatGPT/video_chatgpt/demo/demo_sample_videos  - this corresponds to the Docker volume mapping
responsefolder="/"
filename="sample_demo_22.mp4"
prompt="What is this video about? Provide a detailed description."
#prompt="What instrument is in the video?"

analysevideos(filename,prompt,responsefolder)
