import maadsbml
import numpy as np

def finddist(filename,varname,dataarr,folderpath,imgname,fast=1,topdist=6):
    status,dist,bestdist,alldata=maadsbml.finddistribution(filename,varname,dataarr,folderpath,imgname,fast,topdist)
    print(status)

def genarray():
    mu, sigma = 1, 10.5 # mean and standard deviation
    data = np.random.normal(mu, sigma, 10000)
    return data
    

# Example File 1
filename="body_fat.csv"
# The variable for distributional analysis in body_fat.csv
varname="%Fat"
# Example file 2
filename="weight_height.csv"
# The variable for distributional analysis in weight_height.csv
varname="Height"
# Folder path to save output.  Enter valid path, or it will be saved in current directory.
folderpath='.'
# name of file
imgname="bml"

# We will generate a random array for distributional analysis but we could comment this out and use the above files or any other data
dataarr = genarray()
varname="Sample Data"
# here we are using 1 for FAST distribution analysis using the most common distributions
# 7 to print the TOP 7 distributions in the image and JSON
# Use either filename or dataarr NOT both
filename=""
try:
 finddist(filename,varname,dataarr,folderpath,imgname,1,7)
except Exception as e:
  print(e)  
