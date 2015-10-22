#############################################################################################
#CaPAUpdate.py downloads any new CaPA data to wxData, it then looks for the most recent
#r2c file and appends any updated data to it, by converting grib2 files from the EC datamart

#############################################################################################

import os
import datetime
from urllib2 import urlopen
import argparse
import shutil
import pyEnSim.pyEnSim as pyEnSim
import re


#define some helper functions
#checks to see if a directory exists and builds it if it does not.
def build_dir(directory):
    d = os.path.dirname(directory)
    if not os.path.exists(d):
        os.makedirs(d)
      
#returns a DateTime hours hours from midnight today
def getDateTime(hours):
    tm = datetime.datetime.now()
    newdate = datetime.datetime(tm.year, tm.month, tm.day, 0, 0, 0)
    newdate = newdate + datetime.timedelta(hours=hours)
    return newdate
    
class args(object):
  pass

#Get command line arguments
data = args()
parser = argparse.ArgumentParser()
parser.add_argument('--RepoPath',help="path to store grib files")
parser.add_argument('--startHour', choices = ['00','12'], default='00', help="The hour to pull from: 00 or 12")
parser.add_argument('--historicalStartDate',help="historical start date.")

parser.parse_args(namespace=data)

#Initialize some useful variables
now = datetime.datetime.now()
ScriptDir = os.path.split(os.path.abspath(__file__))[0]
timeVar = getDateTime(int(data.startHour))
timestamp = timeVar.strftime("%Y%m%d%H")
RepoPath = data.RepoPath + "/"

url = 'http://dd.weather.gc.ca/analysis/precip/rdpa/grib2/polar_stereographic/06/'
build_dir(ScriptDir + "\\..\\wxData\\CaPA\\") 
filename_nomenclature = 'CMC_RDPA_APCP-006-0700cutoff_SFC_0_ps10km_'

#Download grib2 files from DataMart  
 #While an online version exists and a local version does not download then repeat for 6 hours earlier
print "Downloading grib files from DataMart"
while (True):
    try:
        #print url + '/CMC_RDPA_APCP-006-final_SFC_0_ps10km_' + timestamp + '_000.grib2'
        #urlopen(url + '/CMC_RDPA_APCP-006-final_SFC_0_ps10km_' + timestamp + '_000.grib2') #old nomenclature
        urlopen(url + '/' + filename_nomenclature + timestamp + '_000.grib2')
        if not os.path.exists(RepoPath + filename_nomenclature + timestamp + "_000.grib2"):
            os.system("wget -O " + RepoPath + filename_nomenclature + timestamp + "_000.grib2 " + url + "/" + filename_nomenclature + timestamp + "_000.grib2")
            timeVar = timeVar - datetime.timedelta(hours = 6)
            timestamp = timeVar.strftime("%Y%m%d%H")
        else:
            break
    except:
        break
         #Usually means that there is no more to download, ie. no online version exists
print "stopped pulling files at " + url + '/' + filename_nomenclature + timestamp + '_000.grib2'



#    Append most recent data to existing r2c file *************************************

#check if base r2c file exists
currentyear = datetime.date.today().year
r2cfile = str(currentyear) + '0101_met.r2c'
existingr2c = str(ScriptDir) + "/../wxData/CaPA/" + str(r2cfile)
print existingr2c
if not os.path.isfile(existingr2c):
   print "Error: the base r2c file (" + str(r2cfile) + ") does not exist. Please ensure file is located in Model_Repository/wxData/CaPA "





#Read .r2c file to get the last date
match = re.findall(r':Frame\s+(\d+)\s+\d+\s+(.+)', open(existingr2c).read())
match = match[len(match)-1]
lastindexframe = int(match[0])
lasttimeframe = match[1]
endtimeframe = datetime.datetime.strptime(lasttimeframe, '"%Y/%m/%d %H:%M"') #- datetime.timedelta(hours = 6)
print "endtimeframe is" + str(endtimeframe)

#
#get the timestamp from this morning
todayEnd = getDateTime(int(data.startHour))
print "todayEnd is" + str(todayEnd)


#initialize r2c file from template
dest=pyEnSim.CRect2DCell()
templater2cpath = str(ScriptDir) +"\..\lib\EmptyGridLL.r2c"
dest.SetFullFileName(templater2cpath)
dest.LoadFromFile()
dest.InitAttributes()
   

#loop to convert each frame from grib2 to r2c and append to working r2c file
i = 0
while (todayEnd > endtimeframe):
         i = i + 1
         #iterate r2c frame timestep
         endtimeframe = endtimeframe + datetime.timedelta(hours = 6)
         timestamp = endtimeframe.strftime("%Y%m%d%H")
         
         #get relevant grib file name
         gribname = str(RepoPath) + filename_nomenclature + timestamp + "_000.grib2"
         print gribname

         #load the required grib file
         theGribFile=pyEnSim.CGrib2File()
         timeStep = pyEnSim.CEnSimDateTime()
         theGribFile.SetFullFileName(gribname)
         theGribFile.LoadFromFile()
         theGribFile.InitAttributes()

         #copy the data from the grib file layer (some grib files have multiple layers (ie. ensemble))
         firstRaster = theGribFile.GetChild(0)
         
         #get coordinate system for later use
         cs = firstRaster.GetCoordinateSystem()

         #multiply values by a coefficient if necessary (ie. convert to mm)
         #for k in range(0,firstRaster.GetNodeCount()+1):
         #  firstRaster.SetNodeValue(k, firstRaster.GetNodeValue(k) * 1000)
           
         #create output object from initial template and raster data
         dest.ConvertToCoordinateSystem(cs)
         dest.MapObjectDispatch(firstRaster)
         dest.SetCurrentStep(lastindexframe+i)
         dest.SetCurrentFrameCounter(lastindexframe+i)
         timeStep.Set(endtimeframe.year,endtimeframe.month,endtimeframe.day,endtimeframe.hour,0,0,0)
         dest.SetCurrentStepTime(timeStep)

         #Append to existing r2c file
         dest.AppendToMultiFrameASCIIFile(existingr2c, 0)
         #dest.AppendToMultiFrameASCIIFile("C:\Test_Framework\EC_Operational_Framework\Model_Repository\wxData\CaPA\20140101_met.r2c", 0)
         


#  copy file to working directory  
radclr2c = str(ScriptDir) + "/../wpegr/radcl/" + str(r2cfile)  
shutil.copyfile(existingr2c, radclr2c)
#==============================================================================