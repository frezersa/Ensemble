import datetime
import os
import subprocess
import shutil
import time
import sys
import glob
import argparse
import re
import urllib2
# NRC pyEnSim. must be installed prior to use.
import pyEnSim.pyEnSim as pyEnSim 


def ignore_wxData(src_path,content):
  if ('wxData' in content):
     return 'wxData'
     #Here when test folder found it will passed 
     #to ignore list
  else:
     return []


def parse_configuration_file(configuration_file):
    """
    parse configuration file name:value into a dict.
    """
    
    config_script = open(configuration_file,"r").readlines()
    
    parameter_settings = {}
    
    # ignore '#', these are comments
    for e in config_script:
        if "#" in e or "##" in e:
            continue
        else:
            # discard empty lines
            if e.strip():
                # remove eol
                tmp = e.strip()
                # parse key:name into dict
                key,value = tmp.split(":",1)
                parameter_settings[key]=value
    
    return parameter_settings

    
    
class ConfigParse:
    ''' object to define all parameters in the configuration.txt file'''
    def __init__(self,configurationtext):
    
            ## read configuration text file
        parameter_settings = parse_configuration_file(configurationtext)

        # link parsed configuration file values here. one point to change!
        self.repository_directory = parameter_settings["repository_directory"]
         
        #= directories mapping
        self.configuration_file = configurationtext
        self.tmp_directory = parameter_settings["tmp_directory"]
        self.bin_directory = parameter_settings["bin_directory"]
        self.forecast_directory = parameter_settings["forecast_directory"]
        self.scripts_directory = parameter_settings["scripts_directory"]
        # watflood folder "wpegr"
        self.model_directory = parameter_settings["model_directory"]
        self.model_directory = os.path.join(self.repository_directory,self.model_directory)
        # forecast & capa data
        self.weather_data_directory = parameter_settings["weather_data_directory"]

        # historic capa data for spinup
        self.historical_capa_path = parameter_settings["historical_capa_path"]

        # historic GEMTemps data for spinup
        self.historical_GEMTemps_path = parameter_settings["historical_GEMTemps_path"]

        #EC Download paths
        self.grib_capa_repo = parameter_settings["grib_capa_repo"]
        self.grib_GEMTemps_repo = parameter_settings["grib_GEMTemps_repo"]
        self.grib_forecast_repo = parameter_settings["grib_forecast_repo"]
         
        #= hec dss db
        self.hec_writer_script = parameter_settings["hec_writer_script"]
         
        #= executables
        self.data_distribution_temperature = parameter_settings["data_distribution_temperature"]
        self.data_distribution_precipitation = parameter_settings["data_distribution_precipitation"]
        self.data_distribution_snow = parameter_settings["data_distribution_snow"]
        self.data_distribution_moist = parameter_settings["data_distribution_moist"]
        self.data_state_variable_streamflow = parameter_settings["data_state_variable_streamflow"]
        self.watflood_executable = parameter_settings["watflood_executable"]
        self.hecdss_vue_path = parameter_settings["hecdss_vue_executable"]

        # location of r scripts
        self.r_script_directory = os.path.join(self.repository_directory,"scripts")

        # r must be added to path. Rscript is name to call from cmd
        self.rscript_path = "Rscript"

        # script names
        # james single script
        self.r_script_lwcb_query = parameter_settings["r_script_lwcb_query"]
        self.r_script_lwcb_PT2query = parameter_settings["r_script_lwcb_PT2query"]
        self.r_script_r2cadjust = parameter_settings["r_script_r2cadjust"]
        self.r_script_lakelevels = parameter_settings["r_script_lakelevels"]
        self.r_script_forecast = parameter_settings["r_script_forecast"]
        self.r_script_ensemblegraphs = parameter_settings["r_script_analysis_ensemble"]
        self.lwcb_db_path = parameter_settings["lwcb_db_path"]


        ## ===== dates
        # spin up dates
        self.spinup_start_date = parameter_settings["spinup_start_date"]
        self.spinup_end_date = parameter_settings["spinup_end_date"]

        # historical dates
        self.historical_start_date = parameter_settings["historical_start_date"]
        self.historical_end_date = parameter_settings["historical_end_date"]

        # forecast start date
        self.forecast_date = parameter_settings["forecast_date"]
        ## ======



        # lwcb db stations
        self.lwcb_station_diver = parameter_settings["lwcb_station_diver"]
        self.lwcb_station_level = parameter_settings["lwcb_station_level"]
        self.lwcb_station_precipitation = parameter_settings["lwcb_station_precipitation"]
        self.lwcb_station_resin = parameter_settings["lwcb_station_resin"]
        self.lwcb_station_resrel = parameter_settings["lwcb_station_resrel"]
        self.lwcb_station_streamflow = parameter_settings["lwcb_station_streamflow"]
        self.lwcb_station_temperature = parameter_settings["lwcb_station_temperature"]
        self.use_resrel = parameter_settings["use_resrel"]
        self.nudge_strmflws = parameter_settings["nudge_strmflws"]


        #= forecast and capa data
        self.use_capa = parameter_settings["use_capa"]
        self.use_GEMTemps = parameter_settings["use_GEMTemps"]

        # pull data
        # start hout for data pull. either 00 or 12. default is 00.
        self.capa_start_hour = parameter_settings["capa_start_hour"]
        self.forecast_start_hour = parameter_settings["forecast_start_hour"] 


        #= watflood configuration files
        # write r script resin/spl png's for analysis
        self.r_graphics_directory = os.path.join(self.repository_directory,"diagnostic")

        # r script names for spl/resin analysis
        self.r_script_analysis_spl = parameter_settings["r_script_analysis_spl"]
        self.r_script_analysis_resin = parameter_settings["r_script_analysis_resin"]

        # location of adjustment scripts

        self.precip_adjust = parameter_settings["precip_adjust"]
        self.temp_adjust = parameter_settings["temp_adjust"]


        


def query_lwcb_db(config_file,start_date,end_date):
    """
    query lwcb db & convert to required tb0 format. 
    
    will use existing R scripts to accomplish. output folders in model directory are hardcoded.
    """
    
    # execute R script. 
    # format to call script is: :: diver -- C:\"Program Files"\R\R-3.0.2\bin\i386\Rscript C:\1_tmp\branches\R\WriteTBOs_modified\LWCBtoTBO.R "C:\1_tmp\branches\R\WriteTBOs_modified" "C:\1_tmp\branches\R\WriteTBOs_modified" "diver" "diver" "2011/01/01" "2012/12/31" "X:/Rlibrary/lwcb_Rimport.mdb" "Root_R, 5"
    # scriptRootDirectory required for relative path in scripts for library import
    
    print "Getting historical data from DB..."
    # res releases
    if config_file.use_resrel == "True":
      cmd = [config_file.rscript_path,
            os.path.join(config_file.r_script_directory, config_file.r_script_lwcb_query),
            config_file.r_script_directory, #1
            config_file.model_directory,#2
            "resrl","rel", #3,4
            start_date, #5
            end_date, #6
            config_file.lwcb_db_path, #7
            config_file.lwcb_station_resrel, #8
            config_file.nudge_strmflws] #9
      subprocess.call(cmd,shell=True)
      
    # diversions
    cmd = [config_file.rscript_path,
          os.path.join(config_file.r_script_directory, config_file.r_script_lwcb_query),
          config_file.r_script_directory,
          config_file.model_directory,
          "diver","diver",
          start_date,
          end_date,
          config_file.lwcb_db_path,
          config_file.lwcb_station_diver,
          config_file.nudge_strmflws]
    subprocess.call(cmd,shell=True)
     
    # levels
    cmd = [config_file.rscript_path,
          os.path.join(config_file.r_script_directory, config_file.r_script_lwcb_query),
          config_file.r_script_directory,
          config_file.model_directory,
          "level","level",
          start_date,
          end_date,
          config_file.lwcb_db_path,
          config_file.lwcb_station_level,
          config_file.nudge_strmflws]
    subprocess.call(cmd,shell=True)
    
    # db precipitation if no capa
    if config_file.use_capa == "False":  
        # precipitation
        cmd = [config_file.rscript_path,
              os.path.join(config_file.r_script_directory, config_file.r_script_lwcb_query),
              config_file.r_script_directory,
              config_file.model_directory,
              "raing","raing",
              start_date,
              end_date,
              config_file.lwcb_db_path,
              config_file.lwcb_station_precipitation,
              config_file.nudge_strmflws]
        subprocess.call(cmd,shell=True)
      
    # resin inflows
    cmd = [config_file.rscript_path,
          os.path.join(config_file.r_script_directory, config_file.r_script_lwcb_query),
          config_file.r_script_directory,
          config_file.model_directory,
          "resrl","rin",
          start_date,
          end_date,
          config_file.lwcb_db_path,
          config_file.lwcb_station_resin,
          config_file.nudge_strmflws]
    subprocess.call(cmd,shell=True)
    

    # stream flow
    cmd = [config_file.rscript_path,
          os.path.join(config_file.r_script_directory, config_file.r_script_lwcb_query),
          config_file.r_script_directory,
          config_file.model_directory,
          "strfw","strfw",
          start_date,
          end_date,
          config_file.lwcb_db_path,
          config_file.lwcb_station_streamflow,
          config_file.nudge_strmflws]
    subprocess.call(cmd,shell=True)
      
    # temperature
    if config_file.use_GEMTemps == "False":
      cmd = [config_file.rscript_path,
            os.path.join(config_file.r_script_directory, config_file.r_script_lwcb_query),
            config_file.r_script_directory,
            config_file.model_directory,
            "tempg","tempg",
            start_date,
            end_date,
            config_file.lwcb_db_path,
            config_file.lwcb_station_temperature,
            config_file.nudge_strmflws]
      subprocess.call(cmd,shell=True)
    
    
    
#gets a DateTime hours hours from midnight this morning
def getDateTime(hours):
    tm = datetime.datetime.now()
    newdate = datetime.datetime(tm.year, tm.month, tm.day, 0, 0, 0)
    newdate = newdate + datetime.timedelta(hours=hours)
    return newdate

    
    
#checks to see if a directory exists and creates it if it does not
def build_dir(directory):
    d = os.path.dirname(directory)
    if not os.path.exists(d):
        os.makedirs(d)
    
    
    
def repo_pull(repos,filePath,timestamp,repo_path):
    #iterate through repo data to pull down files
    today_repo_path = repo_path + "/" + timestamp + "/"
    build_dir(today_repo_path)

    for i, url in enumerate(repos[0]): 
      DeltaTimeStart = int(repos[2][i])
      DeltaTimeEnd = int(repos[3][i])
      DeltaTimeStep = int(repos[4][i])
      for j in range(DeltaTimeStart/DeltaTimeStep,DeltaTimeEnd/DeltaTimeStep + 1):
        #set progress bar
        pbar = (j+1-DeltaTimeStart/DeltaTimeStep)/float((DeltaTimeEnd/DeltaTimeStep + 1)-DeltaTimeStart/DeltaTimeStep) * 40
        sys.stdout.write('\r')
        # the exact output you're looking for:
        sys.stdout.write("[%-40s] %d%%" % ('='*int(pbar), pbar/40*100))
        sys.stdout.flush()
      
        DeltaTime = j * DeltaTimeStep
        #replace %T with the deltaT
        url = repos[0][i].replace('%T', str(DeltaTime).zfill(3))
        name = repos[1][i].replace('%T', str(DeltaTime).zfill(3))
        
        filename = url + name
        #run wget
        if not os.path.isfile(today_repo_path + name):
          try: #download if remote file exists
              #print filename
              urllib2.urlopen(filename) #command to see if remote file can be opened
              os.system("wget -q -O " + today_repo_path + name + " " + filename + " 2> NUL") #use wget to actually download the file
          except urllib2.URLError as e: #do nothing if remote file doesn't exist
              print " Error: File does not exist locally or remotely"
        
          #os.system("wget -q -O " + filePath + "/../wxData/Forecasted/" + timestamp + "/" + name + " " + filename + " 2> NUL")
      print "\n"
          
          
          
def grib2r2c(repos,filePath,datestamp,startHour,repo_path):
      #Initialize some usful variables
      Path = os.path.split(os.path.abspath(__file__))[0]
      today_repo_path = repo_path + "/" + datestamp + startHour + "/"
      #print today_repo_path
      
      
      

      # load a blank r2c that is the template
      dest=pyEnSim.CRect2DCell()
      dest.SetFullFileName(Path + "/../lib/EmptyGridLL.r2c")
      dest.LoadFromFile()
      dest.InitAttributes()

      #Iterate through the repo data, using it to identify downloaded files and convert them to r2c
      #Mostly the same idea as in RepoPull.py     
      
      
      for i, group in enumerate(repos[7]):
          if i == 0: newflag = 1 # because precip at each timestep is calc'd by subtracting cumulative precip ([t] - [t-1]), the first timestep ([t-1]) must be flagged
          if i == 1: newflag = 2 #different flag for second time series because we don't want to append the first frame, only use it for subtracting from the next one
          #print "i = " + str(i) + "  newflag = " + str(newflag) + "\n"
          StitchTimeStart = int(repos[5][i])
          StitchTimeEnd = int(repos[6][i])
          DeltaTimeStep = int(repos[4][i])
          Type = str(repos[8][i])
          Forecast = str(repos[9][i])
          
          # create an object to store each new frame
          theGribFile=pyEnSim.CGrib2File()
          timeStamp = pyEnSim.CEnSimDateTime()
          build_dir(Path + "/../wxData/" + group + "/")
          outFileName = Path + "/../wxData/" + group + "/" + datestamp + "_" + group + ".r2c"
          

          
          for j in range(StitchTimeStart/DeltaTimeStep,StitchTimeEnd/DeltaTimeStep + 1):
            #set progress bar
            pbar = (j+1-StitchTimeStart/DeltaTimeStep)/float((StitchTimeEnd/DeltaTimeStep+1)-StitchTimeStart/DeltaTimeStep) * 40
            sys.stdout.write('\r')
            # the exact output you're looking for:
            sys.stdout.write("[%-40s] %d%%" % ('='*int(pbar), pbar/40*100))
            sys.stdout.flush()
            
            
          
            if Type == "GEM":
            
              if newflag == 0:
                OldFileNamePath = fileNamePath
                
              #get grib file name
              DeltaTime = j * DeltaTimeStep
              date = getDateTime(DeltaTime)
              grouping = repos[7][i].replace('%T', str(DeltaTime).zfill(3))
              fileName = repos[1][i].replace('%T', str(DeltaTime).zfill(3))
              fileNamePath = today_repo_path + fileName
              #print fileNamePath

              #find whether met or tem file
              group = repos[7][i].replace('%T', str(DeltaTime).zfill(3))

              #load grib data into object
              theGribFile=pyEnSim.CGrib2File()
              theGribFile.SetFullFileName(fileNamePath)
              theGribFile.LoadFromFile()
              theGribFile.InitAttributes()
              rasterCount = theGribFile.GetChildrenCount()
              grid = theGribFile.GetChild(0)
              cs = grid.GetCoordinateSystem()
              
              if newflag == 0:
                #load grib data into object
                OldGribFile=pyEnSim.CGrib2File()
                OldGribFile.SetFullFileName(OldFileNamePath)
                OldGribFile.LoadFromFile()
                OldGribFile.InitAttributes()
              
              #Met data is currently expected to be of cumulative 
              if group == 'met':
                if newflag == 0: #don't process if it is the first timestep of the series (0 for regional, 48 for global, because the two series are being stiched together)
                   OldTmp = OldGribFile.GetChild(0)
                   for k in range(0,grid.GetNodeCount()+1):
                     rainvalue = grid.GetNodeValue(k)- OldTmp.GetNodeValue(k)
                     if rainvalue < 0:
                       rainvalue = 0
                     grid.SetNodeValue(k, rainvalue)
                outFileName = Path + "/../wxData/" + group + "/" + datestamp + "_" + group + "_" + Forecast + "-00" + ".r2c"
                    
              
              #convert temp data to Celcius (from Kelvin)
              if group == 'tem':
                for k in range(0,grid.GetNodeCount()+1):
                    grid.SetNodeValue(k, grid.GetNodeValue(k) - 273.15)
                outFileName = Path + "/../wxData/" + group + "/" + datestamp + "_" + group + "_" + Forecast + "-00" + ".r2c"
                      
                #copy data over to r2c file and write output
              dest.ConvertToCoordinateSystem(cs)
              dest.MapObjectDispatch(theGribFile.GetChild(0))
              dest.SetCurrentStep(j+1)
              dest.SetCurrentFrameCounter(j+1)
              timeStamp.Set(date.year,date.month,date.day,date.hour,0,0,0)
              dest.SetCurrentStepTime(timeStamp)
              
              
              if newflag != 2:
                if os.path.isfile(outFileName):
                   dest.AppendToMultiFrameASCIIFile(outFileName, 0)
                else:
                   dest.SaveToMultiFrameASCIIFile(outFileName, 0)
                   
              newflag = 0
            
            if Type == "ENSEMBLE":
           #get grib file name
              if j > 1:
                OldFileNamePath = fileNamePath
                
              DeltaTime = j * DeltaTimeStep
              date = getDateTime(DeltaTime)
              grouping = repos[7][i].replace('%T', str(DeltaTime).zfill(3))
              fileName = repos[1][i].replace('%T', str(DeltaTime).zfill(3))
              fileNamePath = today_repo_path + fileName
              

              #find whether met or tem file
              group = repos[7][i].replace('%T', str(DeltaTime).zfill(3))

              #load grib data into object
              theGribFile=pyEnSim.CGrib2File()
              theGribFile.SetFullFileName(fileNamePath)
              theGribFile.LoadFromFile()
              theGribFile.InitAttributes()
              rasterCount = theGribFile.GetChildrenCount()
              
              if group == 'met':
                if j > 1:
                  #load grib data into object
                  OldGribFile=pyEnSim.CGrib2File()
                  OldGribFile.SetFullFileName(OldFileNamePath)
                  OldGribFile.LoadFromFile()
                  OldGribFile.InitAttributes()
                  
                
                for n in range(0,rasterCount):         
                  tmp = theGribFile.GetChild(n)
                  cs = tmp.GetCoordinateSystem()
                  
                  if j > 1:
                    OldTmp = OldGribFile.GetChild(n)
                    for k in range(0,tmp.GetNodeCount()+1):
                     rainvalue = tmp.GetNodeValue(k)- OldTmp.GetNodeValue(k)
                     if rainvalue < 0:
                       rainvalue = 0
                     tmp.SetNodeValue(k, rainvalue)
                      
                  dest.ConvertToCoordinateSystem(cs)
                  dest.MapObjectDispatch(tmp)
                  dest.SetCurrentStep(j+1)
                  dest.SetCurrentFrameCounter(j+1)
                  timeStamp.Set(date.year,date.month,date.day,date.hour,0,0,0)
                  dest.SetCurrentStepTime(timeStamp)
                  
                  outFileName = Path + "/../wxData/" + group + "/" + datestamp + "_" + group + "_" + Forecast + "-" + str(n).zfill(2) + ".r2c"
                  if os.path.isfile(outFileName):
                    dest.AppendToMultiFrameASCIIFile(outFileName, 0)
                  else:
                    dest.SaveToMultiFrameASCIIFile(outFileName, 0)
                      
                      
              if group == 'tem':
                for n in range(0,rasterCount):         
                  tmp = theGribFile.GetChild(n)
                  cs = tmp.GetCoordinateSystem()
                  
                  for k in range(0,tmp.GetNodeCount()+1):
                      tmp.SetNodeValue(k, tmp.GetNodeValue(k) - 273.15)

                  dest.ConvertToCoordinateSystem(cs)
                  dest.MapObjectDispatch(tmp)
                  dest.SetCurrentStep(j+1)
                  dest.SetCurrentFrameCounter(j+1)
                  timeStamp.Set(date.year,date.month,date.day,date.hour,0,0,0)
                  dest.SetCurrentStepTime(timeStamp)
                  
                  outFileName = Path + "/../wxData/" + group + "/" + datestamp + "_" + group + "_" + Forecast + "-" + str(n).zfill(2) + ".r2c"
                  if os.path.isfile(outFileName):
                     dest.AppendToMultiFrameASCIIFile(outFileName, 0)
                  else:
                     dest.SaveToMultiFrameASCIIFile(outFileName, 0)
          sys.stdout.write('\n')
          


#forecast_date,capa_start_hour,forecast_start_hour,repo_dir,configuration_file
#start_date,    capa_hour, forecast_hour,repo_dir
def query_ec_datamart_forecast(config_file):
    """
    query ec datamart to download and convert data. 
    
    using neil's scripts.
    """
    print "Getting forecast data..."
    split_date = config_file.forecast_date.split("/")
    
    
    #initialize some useful variables
    startHour = '00'
    # now = datetime.datetime.now()
    filePath = os.path.split(os.path.abspath(__file__))[0]
    datestamp = split_date[0] + split_date[1] +split_date[2] 
    timestamp = datestamp + startHour
    
    #Get the repository data from the config file
    getRepos = False
    repos_parent = []
    for line in open(config_file.configuration_file):
      tokens = line.strip().split()
      # deal with white space. indexerror if list is 0 when attempting to pop
      if len(tokens) == 0:
        continue
      if tokens[0] == ':SourceData':
        tokens.pop(0)
        getRepos = True
        repos = []
      elif tokens[0] == ':EndSourceData':  
        tokens.pop(0)
        getRepos = False
        repos_parent.append(repos)
      elif getRepos:
        tokens.pop(0)
        repos.append(tokens)
    #print repos[7]
    

    # Replace special characters (not %T yet) with new values
    for k in range(len(repos_parent)):
      for i, line in enumerate(repos_parent[k]):   
        for j, val in enumerate(line):
          repos_parent[k][i][j] = repos_parent[k][i][j].replace('%Y', split_date[0])
          repos_parent[k][i][j] = repos_parent[k][i][j].replace('%m', split_date[1])
          repos_parent[k][i][j] = repos_parent[k][i][j].replace('%d', split_date[2])
          repos_parent[k][i][j] = repos_parent[k][i][j].replace('%H', startHour)
          
    
    # forecast data
    # pull data
    

    print "Downloading Data.... \n"
    for k in range(len(repos_parent)):
      print "Downloading Forecast File(s): \n" + str(repos_parent[k][1]) 
      repo_pull(repos_parent[k], filePath,timestamp, config_file.grib_forecast_repo)
      print "\n"

     
    # convert to watflood r2c
    #first remove old r2c files
    shutil.rmtree(filePath+"/../wxData/met")
    shutil.rmtree(filePath+"/../wxData/tem")
    os.mkdir(filePath+"/../wxData/met")
    os.mkdir(filePath+"/../wxData/tem")

    
    print "Converting Data.... \n"
    for k in range(len(repos_parent)):
      print "Converting Forecast File(s): \n" + str(repos_parent[k][1]) 
      #for j in range(len(repos_parent[k])):
        #print str(j) + ":    " + str(repos_parent[k][j])
        #print "\n"
      print datestamp
      grib2r2c(repos_parent[k], filePath, datestamp, startHour, config_file.grib_forecast_repo)
      
       
    
    # query_ec_datamart_hindcast(historical_start_date,capa_start_hour)
    #def query_ec_datamart_hindcast(start_date,capa_hour,repository_directory,scripts_directory):
def query_ec_datamart_hindcast(config_file):
    
    # capa data
    # always pull capa data

    # generate r2c from grib2
    print "Getting Precipitation Data /n"
    cmd = ["python",
          os.path.join(config_file.repository_directory, config_file.scripts_directory,"CaPAUpdate.py"),
          "--RepoPath", config_file.grib_capa_repo,
          "--startHour",config_file.capa_start_hour,
          "--historicalStartDate",config_file.historical_start_date]
    subprocess.call(cmd,shell=True)
        
    #GEM Temperature Data
    print "Getting Temperature Data /n"
    cmd = ["python",
          os.path.join(config_file.repository_directory, config_file.scripts_directory,"TemperatureUpdate.py"),
          "--RepoPath", config_file.grib_GEMTemps_repo]
    subprocess.call(cmd,shell=True)
    
    #create YYYYMMDD_dif.r2c file from temperature file
    print "Calculating YYYYMMDD_dif.r2c file /n"
    cmd = [config_file.rscript_path,
          os.path.join(config_file.repository_directory,config_file.scripts_directory,"tempdiff.R"),
          os.path.join(config_file.repository_directory,config_file.scripts_directory)]
    subprocess.call(cmd,shell=True)
    



def generate_distribution_event_file(config_file, resume_toggle = "False", tbc_toggle = "False"):
    """
    creates event file with :noeventstofollow set to 0. used to run distribution executables.
    
    file must be created prior to watflood model. this event file is overwritten after distribution executables with
    updated file for watflood.
    """
    
    # usage: EventGenerator.py [-h] [-FS FORECASTSTART] [-f FLAG FLAG] YearStart [-fd forecastdates]
    # generate the historical event file from jan 1 up to yesterday of forecast start date. must supply "-fd" to ensure event file to follow name is correct. 
    # set the :noeventstofollow to 0.
    if resume_toggle == "True" and tbc_toggle == "True":
      cmd = ["python",
            os.path.join(config_file.repository_directory, config_file.scripts_directory, "EventGenerator.py"),
            "-f", ":noeventstofollow", "0",
            "-f", ":resumflg", "y",
            "-f", ":tbcflg", "y",
            "-fd", config_file.forecast_date,
            "-spinup", "False", config_file.historical_start_date]
      subprocess.call(cmd,shell=True)
    
    elif resume_toggle == "False" and tbc_toggle == "False":
      cmd = ["python",
            os.path.join(config_file.repository_directory, config_file.scripts_directory, "EventGenerator.py"),
            "-f", ":noeventstofollow", "0",
            "-f", ":resumflg", "n",
            "-f", ":tbcflg", "n",
            "-fd", config_file.forecast_date,
            "-spinup", "False", config_file.historical_start_date]
      subprocess.call(cmd,shell=True)
      
    elif resume_toggle == "True" and tbc_toggle == "False":
      cmd = ["python",
            os.path.join(config_file.repository_directory, config_file.scripts_directory, "EventGenerator.py"),
            "-f", ":noeventstofollow", "0",
            "-f", ":resumflg", "y",
            "-f", ":tbcflg", "n",
            "-fd", config_file.forecast_date,
            "-spinup", "False", config_file.historical_start_date]
      subprocess.call(cmd,shell=True)
      
    elif resume_toggle == "False" and tbc_toggle == "True":
      cmd = ["python",
            os.path.join(config_file.repository_directory, config_file.scripts_directory, "EventGenerator.py"),
            "-f", ":noeventstofollow", "0",
            "-f", ":resumflg", "n",
            "-f", ":tbcflg", "y",
            "-fd", config_file.forecast_date,
            "-spinup", "False", config_file.historical_start_date]
      subprocess.call(cmd,shell=True)
      


    

def generate_model_event_files_forecast(config_file):
    """
    create watflood model event files for historic & forecast. 
    
    update the historical event flag :resumflg to 'y'
    """
    print "Generating event files and executing WATFLOOD..."
    # usage: EventGenerator.py [-h] [-FS FORECASTSTART] [-f FLAG FLAG] YearStart [-fd forecastdates]
    # generate the historical event file. must supply "-fd" to ensure event file to follow name is correct.
    # set the :resumflg = y

    #get list of met files
    met_list = sorted(os.listdir(config_file.model_directory + "/radcl"))
    tempr_list = os.listdir(config_file.model_directory + "/tempr")
    tem_list = sorted([s for s in tempr_list if "tem" in s])
    dif_list = sorted([s for s in tempr_list if "dif" in s])
    #loop through list of met files, substituting each into a new event file, then run watflood and save results
    
    #delete contents of folder first
    forecast_folder = config_file.repository_directory + "/forecast/"
    for the_file in os.listdir(forecast_folder):
      file_path = os.path.join(forecast_folder, the_file)
      try:
        if os.path.isfile(file_path):
          os.unlink(file_path)
      except Exception, e:
        print e
    
    
    for i,metfile in enumerate(met_list):
      print "Running Scenario: " + metfile[13:17]
      # generate the forecast event file
      cmd = ["python",os.path.join(config_file.repository_directory,config_file.scripts_directory,"EventGenerator.py"),"-FS",config_file.forecast_date,
          "-f",":resumflg","y",
          "-f",":griddedrainfile","radcl\\" + metfile, 
          "-f",":griddedtemperaturefile","tempr\\" + tem_list[i],
          "-f",":griddeddailydifference","tempr\\" + dif_list[i],
          "-fd","1900/01/01","-f",":noeventstofollow","0",
          config_file.historical_start_date]
      subprocess.call(cmd,shell=True)
    
      #run watflood
      execute_watflood(config_file)
    
      #save results to common folder
      shutil.copyfile(config_file.model_directory + "/results/spl.csv",config_file.repository_directory + "/forecast/" + "spl" + str(metfile[13:17]) + ".csv")
      shutil.copyfile(config_file.model_directory + "/results/resin.csv",config_file.repository_directory + "/forecast/" + "resin" + str(metfile[13:17]) + ".csv")
      


def generate_forecast_files(config_file):
    """
    generates following 4 forecast files. streamflow, reserviour release, resevoir inflows & diversions. following :endheader tag, 10 days of rows populated
    with either -1 or 0. 
    """
    
    print "Generating streamflow, reservoir and diversion forecast files..."
    
    def generate_forecast_streamflow_file():
        """
        sets stations to -1 to only get natural flows from resevoirs.
        
        forecast startdate required
        """
        
        # forecast start date used
        # --start hour is optional. not implemented as it defaults to 00.
        cmd = ["python",os.path.join(config_file.repository_directory,
                                    config_file.scripts_directory,
                                    "StreamflowGenerator.py"),
                                    config_file.forecast_date]
        subprocess.call(cmd,shell=True)
    
    
    def generate_forecast_releases_file():
        """
        sets station co-efficents to 0.
        
        forecast startdate required & --forecast flag to set true to write 0 coffiecents for selected stations in config file.
        """
        
        # --hour is optional. not implemented as it defaults to 00. --forecast to write zeros in coeffiecents for selected stations in config file.
        cmd = [config_file.rscript_path,os.path.join(config_file.r_script_directory,config_file.r_script_lwcb_query),
                                          config_file.r_script_directory,config_file.model_directory,"resrl","rel",
                                          config_file.forecast_date,config_file.forecast_date,
                                          config_file.lwcb_db_path,config_file.lwcb_station_resrel]
        subprocess.call(cmd,shell=True)
    
    
    def generate_forecast_inflows_file():
        """
        sets stations to -1.
        
        forecast startdate required
        """
        
        cmd = ["python",os.path.join(config_file.repository_directory,config_file.scripts_directory,"ResInflowGenerator.py"),config_file.forecast_date]
        subprocess.call(cmd,shell=True)
    
    
    
    def generate_forecast_diversions_file():
        """
        sets diversion file to 0.
        
        forecast startdate required
        """
        
        # generate div_pt2, write to level directory
        # cmd = ["python",os.path.join(repository_directory,scripts_directory,"GenericTemplateWritter.py"),"TEMPLATE_div.tb0",os.path.join(model_directory,"diver"),"div.tb0",forecast_date]
        # subprocess.call(cmd,shell=True)
        cmd = [config_file.rscript_path,os.path.join(config_file.r_script_directory,config_file.r_script_lwcb_query),config_file.r_script_directory,
              config_file.model_directory,"diver","diver",config_file.forecast_date,config_file.forecast_date,
              config_file.lwcb_db_path,config_file.lwcb_station_diver]
        subprocess.call(cmd,shell=True)

      
    # diversions


    
    generate_forecast_streamflow_file()
    generate_forecast_releases_file()
    generate_forecast_inflows_file()
    generate_forecast_diversions_file()

    

def generate_historic_files(start_date,repository_directory,scripts_directory):
    """
    creates historical files necessary for operational use. generated from template files found in model_repository/lib.
    """
    
    # generates historical release file using a template.
    # --hour is optional. not implemented as it defaults to 00.
    cmd = ["python",os.path.join(repository_directory,scripts_directory,"ResReleaseGen.py"),start_date]
    subprocess.call(cmd,shell=True)

   

    
def calculate_distributed_data(config_file, snow, moist):
    """
    run distribution models. moist.exe, snw.exe are always run, ragmet.exe, tmp.exe only if no capa/ no GEMtemps selected by
    user in configuration file.
    
    executables must be run from the root of model directory.
    """
    print "Calculating Distributed Data"
    
    # initial directory
    initial_directory = os.getcwd()
    
    # change directory to root of model directory
    os.chdir(os.path.join(config_file.repository_directory, config_file.model_directory))
    
    # run distribution executables
    # ragmet
    if config_file.use_capa != "True":
        # ragment exe. no capa. using lwcb prepication.
        cmd = [os.path.join(config_file.repository_directory,
                            config_file.bin_directory,
                            config_file.data_distribution_precipitation)]    
        subprocess.call(cmd,shell=True)
        
    # tmp exe
    if config_file.use_GEMTemps != "True":
      cmd = [os.path.join(config_file.repository_directory,
                          config_file.bin_directory,
                          config_file.data_distribution_temperature)]   
      subprocess.call(cmd,shell=True)
	
    # snow exe
    if snow == "True":
      cmd = [os.path.join(config_file.repository_directory,
                          config_file.bin_directory,
                          config_file.data_distribution_snow)]   
      subprocess.call(cmd,shell=True)
	
    # moist exe
    if moist == "True":
      cmd = [os.path.join(config_file.repository_directory,
                          config_file.bin_directory,
                          config_file.data_distribution_moist)]   
      subprocess.call(cmd,shell=True)
    


    # reset directory to initial
    os.chdir(initial_directory)

    

def update_model_folders(config_file):
    """
    update model folders with files where appropriate. review comments below.
    """
    def copytree(src, dst, symlinks=False, ignore=None):
      for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, symlinks, ignore)
        else:
            shutil.copy2(s, d)
    
    #= move forecast generated r2c files into appropriate model folders. data is always generated. 
    # data currently created in wxData/met --> model_directory/radcl & wxData/tem --> model_directory/tempr
    # copy precipitation
    # get file name in directory
    forecast_met_directory = os.path.join(config_file.repository_directory, config_file.weather_data_directory, "met")
    current_file = os.listdir(forecast_met_directory)[0]
    copytree(forecast_met_directory, os.path.join(config_file.repository_directory, config_file.model_directory, "radcl"))
    
    # copy temperature
    forecast_tem_directory = os.path.join(config_file.repository_directory, config_file.weather_data_directory,"tem")
    current_file = os.listdir(forecast_tem_directory)[0]
    copytree(forecast_tem_directory,os.path.join(config_file.repository_directory,config_file.model_directory,"tempr"))
    
    #create YYYYMMDD_dif.r2c file from temperature file
    print "Calculating YYYYMMDD_dif.r2c file \n"
    cmd = [config_file.rscript_path, os.path.join(config_file.repository_directory, config_file.scripts_directory, "tempdiff.R"),
                                    os.path.join(config_file.repository_directory, config_file.scripts_directory)]

    subprocess.call(cmd,shell=True)

    

def execute_watflood(config_file):
    """
    execute waterflood model, current directory must be model directory.
    """

    # must change to root of model directory
    os.chdir(os.path.join(config_file.repository_directory,config_file.model_directory))    
    
    cmd = [os.path.join(config_file.repository_directory,config_file.bin_directory,config_file.watflood_executable)]
    subprocess.call(cmd,shell=True)

    

def generate_spinup_event_files(config_file,start_date,end_date):
    """
    event files specific to spin up. end date is provided as full date to end of last year to lwcb db. must be endYear0101.
    """
    print "Generating Event Files" 
    #Parse Start and end dates
    start_date = datetime.datetime.strptime(start_date,"%Y/%m/%d")
    end_date = datetime.datetime.strptime(end_date,"%Y/%m/%d")
    
    start_year = int(datetime.datetime.strftime(start_date,"%Y"))
    end_year = int(datetime.datetime.strftime(end_date,"%Y"))
    
    #Execute if only a single year for spinup
    if start_year == end_year:
      event_start = str(start_year) + "/01/01"
      cmd = ["python",
            os.path.join(config_file.repository_directory, config_file.scripts_directory,"EventGenerator.py"),
            "-fd","1900/01/01",
            "-f",":noeventstofollow","0",event_start] #1900 is a dummy year that needs to be entered for the EventGenerator to work
      subprocess.call(cmd,shell=True)
      return #get out of function if single year

    #get range of years
    Spinup_Years = range(start_year,end_year+1)
    

    
    #usage: EventGenerator.py [-h] [-FS FORECASTSTART] [-f FLAG FLAG] YearStart [-fd forecastdates]
    #generate the historical event file from jan 1 up to yesterday of forecast start date. must supply "-fd" to ensure event file to follow name is correct. 
    #loop through each year
    for i,event_year in enumerate(Spinup_Years):
      event_start = str(event_year) + "/01/01"
      
      
      yearstofollow = [str(s) for s in range(event_year+1,end_year+1)]
      stringtoappend = "/01/01"
      eventstofollow = [s + stringtoappend for s in yearstofollow]
      pretty_eventstofollow = ' '.join(eventstofollow)

      #first event file
      if i == 0:
        cmd = ["python",
              os.path.join(config_file.repository_directory, config_file.scripts_directory,"EventGenerator.py"),
              "-fd",pretty_eventstofollow,
              "-f",":noeventstofollow",str(len(eventstofollow)),event_start]
        
      if i!= 0:
        #middle event files
        if event_year != (end_year):
          cmd = ["python",
                os.path.join(config_file.repository_directory, config_file.scripts_directory,"EventGenerator.py"),
                "-fd",pretty_eventstofollow,
                "-f",":noeventstofollow","0",event_start,
                "-spinup","True"]
                
        #last event file
        if event_year == (end_year):
          cmd = ["python",
                os.path.join(config_file.repository_directory, config_file.scripts_directory,"EventGenerator.py"),
                "-f",":noeventstofollow","0",
                "-f",":tbcflg","y",
                "-fd",event_start,
                "-spinup","True",event_start]
          
      subprocess.call(cmd,shell=True)
     

    

def generate_spinup_releases_file(start_date,end_date,repository_directory,scripts_directory):
        """
        creates 2 release files based on template.
        """
                
        # --hour is optional. not implemented as it defaults to 00.
        cmd = ["python",os.path.join(repository_directory,scripts_directory,"ResReleaseGen.py"),start_date]
        subprocess.call(cmd,shell=True)
        
        # creates second year release file with correct date of YYYY0101
        tmp_yyyy = end_date.split("/")[0]
        start_date = "%s/%s/%s" %(tmp_yyyy,"01","01")
        
        # --hour is optional. not implemented as it defaults to 00.
        cmd = ["python",os.path.join(repository_directory,scripts_directory,"ResReleaseGen.py"),start_date]
        subprocess.call(cmd,shell=True)


        
def generate_spinup_generic_files(config_file,start_date,end_date):
    """
    generates generic data files only for spin up. files are _ill.pt2/crs.pt2 & psm.pt2. generated from templates at /../lib/
    
    2 files for each, based on start/end pull YYYY
    """
    
    print "Generating snow and moist files"
    tmp_yyyy = end_date.split("/")[0]
    end_date = "%s/%s/%s" %(tmp_yyyy,"01","01")
    
    
    # generate crs.pt2, write to snow1 directory
    cmd = ["python",
          os.path.join(config_file.repository_directory, config_file.scripts_directory, "GenericTemplateWritter.py"),
          "TEMPLATE_swe.r2c",
          os.path.join(config_file.model_directory,"snow1"),"swe.r2c",start_date]
    subprocess.call(cmd,shell=True)
       
    # generate psm.pt2, write to moist directory
    cmd = ["python",
          os.path.join(config_file.repository_directory,config_file.scripts_directory,"GenericTemplateWritter.py"),
          "TEMPLATE_gsm.r2c",
          os.path.join(config_file.model_directory,"moist"),"gsm.r2c",start_date]
    subprocess.call(cmd,shell=True)



    
def clean_up(model_directory,weather_data_directory,r_graphics_directory):
    """
    removes files from folders prior to execution of framework.
    """
    print "Cleaning up old files..."
    

    directories = ["diver","event","level","moist","radcl","raing","resrl","results","snow1","strfw","tempg","tempr"]
        
    # delete folders in model directory. removes all files.
    for i in directories:
        if os.path.exists(os.path.join(model_directory,i)):
          shutil.rmtree(os.path.join(model_directory,i))
    
    # remove forecast weather data r2c's
    # files from met/ & /tem dirs
    path = os.path.join(weather_data_directory,"tem","*.*")
    files = glob.glob(path)
    for i in files:
        os.remove(i)
    
    path = os.path.join(weather_data_directory,"met","*.*")
    files = glob.glob(path)
    for i in files:
        os.remove(i)
    
    # remove r generate analysis png's
    path = os.path.join(r_graphics_directory,"*.*")
    files = glob.glob(path)
    for i in files:
        os.remove(i)
    
    # create blank directories in model directory
    for i in directories:
        os.mkdir(os.path.join(model_directory,i))
    

    
def spinup_capa(config_file,spinup_start_date,spinup_end_date):
    """
    utilize historical capa data in model spinup.
    
    historical capa data is expected to be in r2c format. file signature must be YYYYMMDD_met.r2c.
    """
    
    print "Copying CaPA Files to Spin-up Directory"
    # convert user spinup dates to start from jan01. capa data in this format.
    start_year = int(spinup_start_date.split("/")[0])
    end_year = int(spinup_end_date.split("/")[0])
    
    #get range of years
    Spinup_Years = range(start_year,end_year+1)
    
    #loop through years and copy file
    for i,Year in enumerate(Spinup_Years):
      start_date = str(Year) +"0101_met.r2c"
      
      # copy capa to model directory wpegr/radcl
      shutil.copy(os.path.join(config_file.historical_capa_path,start_date),
                  os.path.join(config_file.model_directory,"radcl"))
    
    
    
def spinup_GEMTemps(config_file, spinup_start_date, spinup_end_date):
    """
    utilize historical capa data in model spinup.
    
    historical capa data is expected to be in r2c format. file signature must be YYYYMMDD_tem.r2c.
    """
    
    print "Copying GEMTemps Files to Spin-up Directory"
    # convert user spinup dates to start from jan01. capa data in this format.
    start_year = int(spinup_start_date.split("/")[0])
    end_year = int(spinup_end_date.split("/")[0])
    
    #get range of years
    Spinup_Years = range(start_year,end_year+1)
    
    #loop through years and copy file
    for i,Year in enumerate(Spinup_Years):
      start_date_tem = str(Year) +"0101_tem.r2c"
      start_date_dif = str(Year) +"0101_dif.r2c"
      
      # copy capa to model directory wpegr/radcl
      shutil.copy(os.path.join(config_file.historical_GEMTemps_path, start_date_tem),
                  os.path.join(config_file.model_directory,"tempr"))
      shutil.copy(os.path.join(config_file.historical_GEMTemps_path, start_date_dif),
                  os.path.join(config_file.model_directory,"tempr"))
    
    

def generate_analysis_graphs(config_file,
                              resin="NA",
                              spl="NA",
                              start_date="NA",
                              end_date="NA",
                              spinup="False"):
    """
    generates R daily graphics based on output of model resin & spl png files. output to /diagnostic folder
    """
    print "Generating Deterministic inflow and streamflow plots..."
    
    #= resin comparison graphic    
    # convert historical date from yyyy/mm/dd to yyyy-mm-dd
    tmp = config_file.spinup_start_date.split("/")
    if start_date == "NA":
      start_date = "%s-%s-%s" %(tmp[0],tmp[1],tmp[2])

    # resin.csv
    if resin == "NA":
      resin = os.path.join(config_file.model_directory,"results","resin.csv")
    spinup_resin = spinup
    
    if not spinup =="False":
      spinup_resin = os.path.join(spinup,"wpegr","results","resin.csv")
      
    cmd = [config_file.rscript_path,
          os.path.join(config_file.r_script_directory, config_file.r_script_analysis_resin),
          config_file.r_script_directory,
          config_file.r_graphics_directory,
          resin,
          start_date,
          end_date,
          spinup_resin]
    subprocess.call(cmd,shell=True)
      
    #= spl comparison graphic
    # convert historical date from yyyy/mm/dd to yyyy-mm-dd
    tmp = config_file.spinup_start_date.split("/")
    if start_date == "NA":
      start_date = "%s-%s-%s" %(tmp[0],tmp[1],tmp[2])

    # spl.csv
    if spl == "NA":
      spl = os.path.join(config_file.model_directory,"results","spl.csv")
    spinup_spl = spinup
    if not spinup =="False":
      spinup_spl = os.path.join(spinup,"wpegr","results","spl.csv")
    cmd = [config_file.rscript_path,
          os.path.join(config_file.r_script_directory,config_file.r_script_analysis_spl),
          config_file.r_script_directory,
          config_file.r_graphics_directory,
          spl,
          start_date,
          end_date,spinup_spl]
    subprocess.call(cmd,shell=True)
    
    
    
def generate_ensemble_graphs(r_script_directory,r_script_ensemble,r_graphics_directory):
    """
    generates R dailiy graphics based on output of model resin & spl png files. output to /diagnostic folder
    """
    
    print "generating probablistic data"
    cmd = [rscript_path,os.path.join(r_script_directory,r_script_ensemble),r_script_directory]
    #"rscript C:\Ensemble_Framework\EC_Operational_Framework\Model_Repository\scripts\Ensemble_plot.R"
    subprocess.call(cmd,shell=True)
    

    
    
def generate_meteorlogical_graphs(r_script_directory,r_script_forecast,r_graphics_directory,repository_directory,scripts_directory):
    """
    generates R dailiy graphics based on output of model resin & spl png files. output to /diagnostic folder
    """
    

    print "Generating meteorlogical plots..."
    tmp = forecast_date.split("/")
    date_str = "%s%s%s" % (tmp[0],tmp[1],tmp[2])
    met_str_forecast = os.path.join(model_directory,"radcl",date_str + "_met_1-00.r2c")
    tem_str_forecast = os.path.join(model_directory,"tempr",date_str + "_tem_1-00.r2c")
    
    tmp = historical_start_date.split("/")
    start_date = "%s%s%s" %(tmp[0],tmp[1],tmp[2])
    source_dir = os.path.join(os.path.dirname(repository_directory),"Model_Repository_hindcast_adjusted")
    met_str_hindcast = os.path.join(source_dir,"wpegr","radcl","Orig_" + start_date + "_met.r2c")
 
    cmd = [rscript_path,os.path.join(r_script_directory,r_script_forecast),r_script_directory,r_graphics_directory,met_str_forecast,tem_str_forecast,met_str_hindcast]
    subprocess.call(cmd,shell=True)
    
      


def copy_resume(config_file,source_dir): #source dir is the name of the folder where the results come from (ex. Model_Repository_Spinup)
    #get full path of source directories
    print "Copying resume files from " + source_dir + "...." + "\n"
    
    
    source_dir = os.path.join(os.path.dirname(config_file.repository_directory),source_dir)
    
    #delete \wpegr\flowinit.r2c,soilinit.r2c,resume.txt if exists
    resume_files = ["flow_init.r2c","soil_init.r2c","resume.txt","lake_level_init.pt2"]
    del_items = []
    make_items = []
    
    for i in resume_files:
      del_path = os.path.join(config_file.repository_directory,"wpegr",i)
      del_items.append(del_path)
      
      make_path = os.path.join(source_dir,"wpegr",i)
      make_items.append(make_path)
        
    # delete \wpegr\level\20140101_ill.pt2 in dest directory if exists
    tmp = config_file.historical_start_date.split("/")
    ill_file = "%s%s%s" %(tmp[0],tmp[1],tmp[2]) + "_ill.pt2"
    ill_path = os.path.join(config_file.repository_directory,"wpegr","level",ill_file)
    del_items.append(ill_path)
    
    # make_path = os.path.join(source_dir,"wpegr","level",tem_file)
    #make_items.append(del_path)
    
    for d in del_items: 
      if os.path.exists(d):
        
        os.remove(d)
        
    #copy \wpegr\flowinit.r2c,soilinit.r2c,resume.txt to dest directory from source directory
    for m in range(len(make_items)):
      shutil.copyfile(make_items[m],del_items[m])
    
    #create and copy 20140101_ill.pt2 (use rscript)
    cmd = [config_file.rscript_path,os.path.join(config_file.r_script_directory,config_file.r_script_lakelevels),config_file.r_script_directory,os.path.join(source_dir,"wpegr/results/lake_sd.csv"),ill_path]
    #subprocess.call(cmd,shell=True)
    
    print "\n"
    
    
    
def generate_dss(hecdss_vue_path,r_script_directory,hec_writer_script):
    inputfile = os.path.join(r_script_directory,"../diagnostic/Prob_forecast.csv")
    outputfile = os.path.join(r_script_directory,"../diagnostic/HECfile.dss")
    
    if not os.path.isfile(inputfile):
      print "Error: the input file: '" + str(inputfile) + "' does not exist \n and hence a DSS file cannot be created. Please ensure file 'Prob_forecast.csv' exists in the diagnostic directory"

    cmd = [hecdss_vue_path,os.path.join(r_script_directory,hec_writer_script),outputfile,inputfile]
    #cmd = ["C:\Program Files (x86)\HEC\HEC-DSSVue\HEC-DSSVue.exe","C:\Test_Framework\EC_Operational_Framework\Model_Repository\scripts\Writer_hec_dss_prob.py","C:/Test_Framework/EC_Operational_Framework/Model_Repository/diagnostic/HECfile.dss","C:/Test_Framework/EC_Operational_Framework/Model_Repository/diagnostic/Prob_forecast.csv"]
    
    subprocess.call(cmd,shell=True)

    

# ===== main functions to run spinup & forecast
  #model_spinup(spinup_start_date,spinup_end_date,historical_capa_path,model_directory,use_capa,use_resrel,nudge_strmflws)

def model_spinup(config_file):
    # creates event files required
    generate_spinup_event_files(config_file,
                                config_file.spinup_start_date, 
                                config_file.spinup_end_date)
    
    # create release file (not needed anymore, commented out)
    #generate_spinup_releases_file(spinup_start_date,spinup_end_date)
    
    # # generic files built from template for level/snow/moist
    generate_spinup_generic_files(config_file,
                                  config_file.spinup_start_date,
                                  config_file.spinup_end_date)
    
    # query lwcb data
    query_lwcb_db(config_file,
                  config_file.spinup_start_date,
                  config_file.spinup_end_date)
    
    # spinup using capa
    if config_file.use_capa == "True":
        spinup_capa(config_file,
                    config_file.spinup_start_date,
                    config_file.spinup_end_date)
        
    # spinup using GEMTemps
    if config_file.use_GEMTemps == "True":
        spinup_GEMTemps(config_file,
                        config_file.spinup_start_date,
                        config_file.spinup_end_date)
    
    # generate distributed data
    calculate_distributed_data(config_file,
                               snow="False",
                               moist="False",)
    
    # execute watflood
    execute_watflood(config_file)



   #model_hindcast(historical_start_date,historical_end_date,forecast_date,capa_start_hour,forecast_start_hour)
 
def model_hindcast(config_file):
    """
    default hindcast. 
    """
    
    # query lwcb data
    query_lwcb_db(config_file,
                  start_date = config_file.historical_start_date,
                  end_date = config_file.historical_end_date)
    
    # query ec_datamart
    query_ec_datamart_hindcast(config_file)
    
    # generate watflood text files, initial event file used only for distrubtion executables.
    generate_distribution_event_file(config_file,
                                     resume_toggle = "True", 
                                     tbc_toggle = "True")
      
    # calculate distribute temperature,snow & moisture. precipitation dependent upon if capa selected by user.
    calculate_distributed_data(config_file,
                               snow="False",
                               moist="False",)
      
    # execute watflood
    execute_watflood(config_file)
    

    
def adjust_hindcast(precip_toggle,temp_toggle,repository_directory,scripts_directory):
    """
    applies adjustments to r2c files, executes WATFLOOD and plots results
    """
     
    if precip_toggle == "True":
    #execute precipadjust rscript
      tmp = historical_start_date.split("/")
      met_file = "%s%s%s" %(tmp[0],tmp[1],tmp[2]) + "_met.r2c"
      met_location = os.path.join(model_directory,"radcl",met_file)
      precipadjust_location = os.path.join(repository_directory,"lib",precip_adjust)

      cmd = [rscript_path,os.path.join(r_script_directory,r_script_r2cadjust),r_script_directory, met_location, precipadjust_location, "precipmult" ]
      subprocess.call(cmd,shell=True)
    
    if temp_toggle == "True":
    #execute tempadjust rscript
      tmp = historical_start_date.split("/")
      tem_file = "%s%s%s" %(tmp[0],tmp[1],tmp[2]) + "_tem.r2c"
      tem_location = os.path.join(model_directory,"tempr",tem_file)
      tempadjust_location = os.path.join(repository_directory,"lib",temp_adjust)
      
      cmd = [rscript_path,os.path.join(r_script_directory,r_script_r2cadjust),r_script_directory, tem_location, tempadjust_location, "tempadd" ]
      subprocess.call(cmd,shell=True)
      
    # execute watflood
    execute_watflood(config_file)
    
    #create plots
    generate_analysis_graphs(forecast_date,historical_start_date,model_directory,"NA","NA",r_script_directory,r_graphics_directory,r_script_analysis_resin,r_script_analysis_spl,"NA","NA","False")
    
    
    
def model_forecast(config_file):
    """
    default forecast. no changes to state variables. runs start to finish with no interruptions
    """

    # generate forecast files
    generate_forecast_files(config_file)
    
    # query ec_datamart
    query_ec_datamart_forecast(config_file)
      
    # move files to appropriate location within model directory.
    update_model_folders(config_file)
      
    # overwrite event file for model run. includes historic and forecast**********************
    #loop through and change the event file for each forecast
    #WATFLOOD is executed in this function
    generate_model_event_files_forecast(config_file)
