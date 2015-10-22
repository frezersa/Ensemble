## execution:       at cmd:> "C:\Program Files (x86)\HEC\HEC-DSSVue\HEC-DSSVue.exe" "C:\Test_Framework\EC_Operational_Framework\Model_Repository\scripts\Writer_hec_dss_prob.py" 

# === modules
import hec.script as hecScript
import hec.heclib as hecLib
import hec.io as hecIo
import java
import datetime
import os
import sys
import time
import sets


  
# # test data work machine
#scriptLocation= "C:\Test_Framework\EC_Operational_Framework\Model_Repository\scripts\Writer_hec_dss_prob.py"
#locationDssDb = "C:\Test_Framework\EC_Operational_Framework\Model_Repository\diagnostic\HECfile.dss"
#locationWatflood_wpegr = "C:\Test_Framework\EC_Operational_Framework\Model_Repository\diagnostic\Prob_forecast.csv"

#= get script location using sys.argv. first item of returned list is script location.
scriptLocation = sys.argv[0]
locationDssDb = sys.argv[1]
locationWatflood_wpegr = sys.argv[2]

# # get directory of script
dirNameScript=os.path.dirname(scriptLocation)



# # ===== setting defined variables 
# # =dss pathname
# # dss pathname components. A-F refer to dss documentation.
# # B=location (station name)
# # D=block start date (01JAN[year])
# # F=comment (denote either "observed" or "estimated")
dssPathName={"A":"LWCB","B":"","C":"FLOW-IN","D":"","E":"1DAY","F":""}


# # = read watflood output resin.csv. releases observed/predicted output. headers provided.
rawdata = open(locationWatflood_wpegr,"r").readlines()


#parse into list
resinDataIn = []
for row in rawdata:
  row = row.strip().split(",")
  row = [s.replace('"','') for s in row] #removed quotes that were inadvertently added
  resinDataIn.append(row)
  


# # remove and store header
header = resinDataIn.pop(0)
header.pop(0) #removes the first blank space 


# # get the forecast start date
earlydate = datetime.date(2100,01,01)

# # log file
logName="log.txt"
fLog=open(os.path.join(dirNameScript,logName),"a")

for timestring in header:
  tmp = timestring.split("-")
  tmp_date = datetime.date(int(tmp[0]),int(tmp[1]),int(tmp[2]))
  if tmp_date < earlydate:
    earlydate = tmp_date
    
startDate_forecast = earlydate



# get row index for required exceedence probability
rownames = []
for row in resinDataIn:
  rownames.append(row[0])
  del row[0]
  


# filter data to include only the required probabilities
filtered_data = []
filtered_rownames = []
for k,v in enumerate(rownames):
    if "50" in v:
        # append index position where "50" found. used to filter data columns
        filtered_data.append(resinDataIn[k])
        filtered_rownames.append(rownames[k])
        
        
        
# convert to floats
float_filtered_data=[]
for row in filtered_data:
  row = [float(i) for i in row]
  float_filtered_data.append(row)
  
  

# ************************Output to HEC-DSS
for lakes,p in enumerate(filtered_rownames):
  # print "The data for: " + str(filtered_rownames[lakes])
  # print float_filtered_data[lakes] 
  
  station = str(filtered_rownames[lakes])
  forecast = float_filtered_data[lakes] 
  

  # open dss database at this location. creates db if name does not exist.
  dssDbLocation = hecLib.dss.HecDss.open(locationDssDb)
  
  # create time series container
  tsc = hecIo.TimeSeriesContainer()
  
  # create full pathname
  dssPathName["B"]=station #station name
  dssPathName["F"]=station#comment
  tsc.fullName = "/" + dssPathName["A"] + "/" + dssPathName["B"] + "/" + dssPathName["C"] + "/" + dssPathName["D"] + "/" + dssPathName["E"] + "/" +dssPathName["F"] + "/"
  
  # set start point for hec dss write date.
  start = hecLib.util.HecTime(startDate_forecast.strftime("%d%b%Y"), "2400")
  
  # number of minutes between each set of consecutive times in the time series. set to 1 day.
  tsc.interval = 1440
  
  # create interval of time for each corresponding inflow value
  times = []
  for value in forecast:
      times.append(start.value())
      start.add(tsc.interval)
  tsc.times = times
  tsc.values = forecast
  tsc.numberValues = len(forecast)
  
  # explicitly set units = CMS (cubic meters per second)
  tsc.units = "CMS"
  
  # explicitly set flow type, constrained by dss. daily average = PER-AVER 
  tsc.type = "PER-AVER"
  dssDbLocation.put(tsc)
  
  
  
# close dss database
dssDbLocation.close()
fLog.write("\n")
fLog.write("%s\t%s" %(time.ctime(),"Successfully populated HEC DSS Database " + locationDssDb))

# close log file
fLog.close()

  

