import maadstml

def analysevideos(filename,prompt,responsefolder):
    url="http://127.0.0.1"
    port="7800"
    
    response=maadstml.videochatloadresponse(url,port,filename,prompt,responsefolder,temperature=0.2,max_output_tokens=512)
    print(response)
# put videos here:
#/mnt/c/maads/privategpt/Video_ChatGPT/video_chatgpt/demo/demo_sample_videos
responsefolder="/"
filename="sample_demo_22.mp4"
prompt="What is this video about?"
prompt="What instrument is in the video?"

analysevideos(filename,prompt,responsefolder)
