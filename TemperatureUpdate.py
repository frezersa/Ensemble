#############################################################################################
#file to download GEM temp forecasts and store in directory for later use
#this script should be run AT LEAST once a day, but ideally twice in order to ensure all the files are retrieved

#############################################################################################

import os
import datetime
import urllib2
import re
import shutil
import argparse
import pyEnSim.pyEnSim as pyEnSim

class args(object):
  pass

#Get command line arguments
data = args()
parser = argparse.ArgumentParser()
parser.add_argument('--RepoPath',help="path to store grib files")

parser.parse_args(namespace=data)

#Initialize some useful variables

RepoPath = data.RepoPath + "/"
now = datetime.datetime.now()
yesterday = now - datetime.timedelta(days=1)

now_datestamp = now.strftime("%Y%m%d")
yesterday_datestamp = yesterday.strftime("%Y%m%d")

dates = [now_datestamp,yesterday_datestamp]



forecast_periods = [00,06,12,18]
time_periods = [000,003]


#storage_dir = 'C:\WR_WTFLD_Framework_D/Model_Repository/wxData/GEMTemps/'
url = 'http://dd.weather.gc.ca/model_gem_regional/10km/grib2/'
filename_nomenclature = 'CMC_reg_TMP_TGL_2_ps10km_'
ScriptDir = os.path.split(os.path.abspath(__file__))[0]
storage_dir = ScriptDir + "/../wxData/GEMTemps/"



#Download grib2 files from DataMart ****************************************************** 
#While an online version exists and a local version does not download then repeat (hours 000 & 003 for all four forecasts)
for i,startperiod in enumerate(forecast_periods):
  for j,starthour in enumerate(time_periods):
    for k,day in enumerate(dates):

      filename = filename_nomenclature + day + str(startperiod).zfill(2) +'_P' + str(starthour).zfill(3) + '.grib2'
      website = url + str(startperiod).zfill(2) + '/' + str(starthour).zfill(3) + '/' + filename
      #print  website + '\n'
      
      if not os.path.exists(RepoPath + filename): #check if file already exists in local directory
          try: #download if remote file exists
            urllib2.urlopen(website) #command to see if remote file can be opened
            os.system("wget -O " + RepoPath + filename + " " + website) #use wget to actually download the file
          except urllib2.URLError as e: #do nothing if remote file doesn't exist
            print " "
          
        

#    Append most recent data to existing r2c file *************************************

#check if base r2c file exists
currentyear = datetime.date.today().year
r2cfile = str(currentyear) + '0101_tem.r2c'
existingr2c = str(storage_dir) + str(r2cfile)
print existingr2c
if not os.path.isfile(existingr2c):
   print "Error: the base r2c file (" + str(r2cfile) + ") does not exist. Please ensure file is located in Model_Repository/wxData/CaPA "





#Read .r2c file to get the last date
match = re.findall(r':Frame\s+(\d+)\s+\d+\s+(.+)', open(existingr2c).read())
match = match[len(match)-1]
lastindexframe = int(match[0])
lasttimeframe = match[1]
endtimeframe = datetime.datetime.strptime(lasttimeframe, '"%Y/%m/%d %H:%M"') #- datetime.timedelta(hours = 6)
print "endtimeframe is: " + str(endtimeframe)

#
#get the timestamp from this morning
todayEnd = datetime.datetime(now.year, now.month, now.day, 0, 0, 0)
print "todayEnd is: " + str(todayEnd)
print "\n"


#initialize r2c file from template
dest=pyEnSim.CRect2DCell()
templater2cpath = str(ScriptDir) +"\..\lib\EmptyGridLL.r2c"
dest.SetFullFileName(templater2cpath)
dest.LoadFromFile()
dest.InitAttributes()
   

# #loop to convert each frame from grib2 to r2c and append to working r2c file
i = 0
while (todayEnd > endtimeframe):
         i = i + 1
         #iterate r2c frame timestep
         timestamp_odd = endtimeframe.strftime("%Y%m%d%H")
         endtimeframe = endtimeframe + datetime.timedelta(hours = 3)
         timestamp_even = endtimeframe.strftime("%Y%m%d%H")
         hourstamp = endtimeframe.strftime("%H")
         
         
         #get relevant grib file name; this is dependent on the hour because the forecasted temps are being used
         if int(hourstamp) in (0,6,12,18):
           gribname = str(RepoPath) + filename_nomenclature + timestamp_even + "_P000.grib2"
           print gribname
           
         if int(hourstamp) in (3,9,15,21):
           gribname = str(RepoPath) + filename_nomenclature + timestamp_odd + "_P003.grib2"
           print gribname

         # #load the required grib file
         theGribFile=pyEnSim.CGrib2File()
         timeStep = pyEnSim.CEnSimDateTime()
         theGribFile.SetFullFileName(gribname)
         
         try: 
         #if the file is corrupted or empty, it won't be converted properly, skip the this file if this is the case 
         #(hence the use of try: and except:)
             theGribFile.LoadFromFile()
             theGribFile.InitAttributes()

             #copy the data from the grib file layer (some grib files have multiple layers (ie. ensemble))
             firstRaster = theGribFile.GetChild(0)
             
             # #get coordinate system for later use
             
             cs = firstRaster.GetCoordinateSystem()

             #multiply values by a coefficient if necessary (ie. convert to mm)
             for k in range(0,firstRaster.GetNodeCount()+1):
              firstRaster.SetNodeValue(k, firstRaster.GetNodeValue(k) - 273.15)
               
             # #create output object from initial template and raster data
             dest.ConvertToCoordinateSystem(cs)
             dest.MapObjectDispatch(firstRaster)
             dest.SetCurrentStep(lastindexframe+i)
             dest.SetCurrentFrameCounter(lastindexframe+i)
             timeStep.Set(endtimeframe.year,endtimeframe.month,endtimeframe.day,endtimeframe.hour,0,0,0)
             dest.SetCurrentStepTime(timeStep)

             # #Append to existing r2c file
             dest.AppendToMultiFrameASCIIFile(existingr2c, 0)
             
         except: 
            pass
         
         


# #  copy file to working directory  
radclr2c = str(ScriptDir) + "/../wpegr/tempr/" + str(r2cfile)  
shutil.copyfile(existingr2c, radclr2c)
# #==============================================================================