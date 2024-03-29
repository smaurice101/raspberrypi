import maadsbml

host='http://localhost'
port=5595

def hypertraining(host,port,filename,dependentvariable,removeoutliers,hasseasonality):
  #def hypertraining(host,port,filename,dependentvariable,removeoutliers=0,hasseasonality=0,summer='6,7,8',winter='11,12,1,2',shoulder='3,4,5,9,10',trainingpercentage=70,shuffle=0,deepanalysis=0,username='admin',timeout=1200,company='otics',password='123',email='support@otics.ca',usereverseproxy=0,microserviceid='',maadstoken='123',mode=0):

  #host,port,
  #filename= raw data file in csv format - Note this file is stored on your host machine the DOCKER container needs to be mapped to this volume using -v
  #dependentvariable= dependent variable name - this is the column name in the csv file
  # the file should have a Date column in the format Month/Day/Year
  #username= you can specify a username
  #mode=0
  #abort=0 set to 1 to abort the whole process, otherwise set to 0.  If Aborting, you should change port to 10000 to FORCE ABORT OF ANY RUNNING PROCESSES  
  #timeout=180 - you can modify this in seconds if your data file is large
  #company= change this to the name of your company
  #removeoutliers= specify 1 or 0, 1=remove outliers, 0 do not remove outliers,
  #hasseasonality= specify 1 or 0 to indicate date is affected by seasonaility - 1 = seasonality, 0 = no seasonality,
  #summer= specify the summer months ie. '6,7,8', or set to -1 for no summer
  #winter= specify winter months i.e. '11,12,1,2', or -1 for no winter
  #shoulder= specify shoulder months i.e. '3,4,5,9,10', or -1 for no shoulder season
  #trainingpercentage= specify training percentage i.e. 70, the value represents a percentage to split training and test
  #shuffle= specify 1 or 0 to shuffle the data, 1= shuffle, 0 = no shuffle
  #deepanalysis= specify 1 or 0, 1=deepanalysis, note this will run through deeper algorithms but will take longer, 0 = no deep analysis, this will
  #password='123', - leave as is
  #email='support@otics.ca', - leave as is
  #usereverseproxy=0, - leave as is
  #microserviceid='', leave as is
  #maadstoken='123' leave as is

  res=maadsbml.hypertraining(host,port,filename,dependentvariable,removeoutliers,hasseasonality)
  print(res)


def hyperprediction(pkey,host,port,inputdata,username):
  
  res=maadsbml.hyperpredictions(pkey,inputdata,host,port,username)
  print(res)
  
def algoinfo(pk):
   res=maadsbml.algodescription(host,port,pk)
   print(res)

def rundemo(demotype):
    # if demotype=1 then Regression will be run
    # if demotype=0 then Classification will be run
   res=maadsbml.rundemo(host,port,demotype)
   print(res)

def abort(host):
    # if demotype=1 then Regression will be run
    # if demotype=0 then Classification will be run
   res=maadsbml.abort(host)
   print(res)


# ############Function Commands
# Algoinfo
pk='admin_aesopowerdemand_csv'
#algoinfo(pk)
pk='admin_aesopowerdemandlogistic_csv'
#algoinfo(pk)

# ############Abort
#abort(host)

# ############Rundemo
rundemo(1)

 ############Hypertraining
filename='aesopowerdemandlogistic.csv'
dependentvariable='AESO_Power_Demand_Label'

#filename='aesopowerdemand.csv'
#dependentvariable='AESO_Power_Demand'

removeoutliers=1
hasseasonality=0

#hypertraining(host,port,filename,dependentvariable,removeoutliers,hasseasonality)


# ############Hyperpredictions
pkey='admin_aesopowerdemand_csv'
#pkey='admin_aesopowerdemandlogistic_csv'

inputdata='5/10/2010,-14.3,-32.0,-12.0'
#hyperprediction(pkey,host,port,inputdata,'admin')

