import maadsbml
import numpy as np

def finddist(filename,varname,dataarr,folderpath,imgname,fast=1,topdist=6):
    status,dist,bestdist,alldata=maadsbml.finddistribution(filename,varname,dataarr,folderpath,imgname,fast,topdist)
    print(status)

def genarray():
    mu, sigma = 1, 10.5 # mean and standard deviation
    data = np.random.normal(mu, sigma, 10000)
    return data
    

filename="body_fat.csv"
varname="%Fat"
filename="weight_height.csv"
varname="Height"
folderpath='C:/MAADS/Companies/firstgenesis/probability distribution'
imgname="bml"
dataarr = []
dataarr = genarray()
finddist(filename,varname,dataarr,folderpath,imgname,1,3)

