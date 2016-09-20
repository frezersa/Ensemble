import os
import datetime
import sys
import multiprocessing
import subprocess
import urllib2
import re
import shutil

import FrameworkLibrary 
import pyEnSim_basics
 
def repo_pull_nomads(repos, filePath, timestamp, repo_path):
    """
    downloads forecast data from nomads repository using wget
    
        Args:
        repos: the source data in a single source from the config file, see below for example
        filePath: the filepath where the scripts are run ex) Q:\WR_Ensemble_dev\A_MS\Repo\scripts
        timestamp: datestamp + start hour, this is currently the config.file date with a static start hour of '00'
        repo_path: path to store all the repo data; currently 'config_file.grib_forecast_repo'
        
    Website:
    http://nomads.ncep.noaa.gov/txt_descriptions/CMCENS_doc.shtml
    http://nomads.ncep.noaa.gov/cgi-bin/filter_cmcens.pl?file=cmc_gep00.t00z.pgrb2af384&lev_surface=on&var_APCP=on&var_TMP=on&subregion=&leftlon=-98&rightlon=-88&toplat=54&bottomlat=46&dir=%2Fcmce.20160830%2F00%2Fpgrb2a
    http://nomads.ncep.noaa.gov/cgi-bin/filter_gens.pl?file=gec00.t00z.pgrb2anl&lev_2_m_above_ground=on&lev_surface=on&var_TMP=on&subregion=&leftlon=-98&rightlon=-88&toplat=54&bottomlat=46&dir=%2Fgefs.20160830%2F00%2Fpgrb2
    
    #Example repos from config file, note substitution parameters (%X) in :FileName
   :SourceData  
   0:URL                http://nomads.ncep.noaa.gov/cgi-bin/              
   1:FileName           filter_%S1.pl?file=%S2gep%E.t%Hz.pgrb2af%T&%query&subregion=&leftlon=-98&rightlon=-88&toplat=54&bottomlat=46&dir=%2F%S3.%Y%m%d%2F00%2Fpgrb2a
   2:DeltaTimeStart     6                                                                          
   3:DeltaTimeEnd       240                                                                         
   4:DeltaTimeStep      6                                                                          
   5:StitchTimeStart    6                                                                          
   6:StitchTimeEnd      240                                                                         
   7:Grouping           tem                                                                        
   8:Type               NOMAD_GFS                                                                        
   9:Forecast           3
   10:num_ensembles     20   
:EndSourceData

    """
    #build repository directory to store the date's files
    today_repo_path = repo_path + "/" + timestamp + "/"
    FrameworkLibrary.build_dir(today_repo_path)



    url = repos[0][0]
    DeltaTimeStart = int(repos[2][0])
    DeltaTimeEnd = int(repos[3][0])
    DeltaTimeStep = int(repos[4][0])
    Source =  repos[8][0]
    Grouping = repos[7][0]
    num_ensembles = int(repos[10][0])
    wget_list = []

    print 'building list of files for download'
    for k in range(1,num_ensembles + 1): #for each ensemble member
        #set progress bar
        pbar = k/float(num_ensembles) * 40
        sys.stdout.write('\r')
        # the exact output you're looking for:
        sys.stdout.write("[%-40s] %d%%" % ('='*int(pbar), pbar/40*100))
        sys.stdout.flush()

        for j in range(DeltaTimeStart/DeltaTimeStep,DeltaTimeEnd/DeltaTimeStep + 1): #for each timestep

            ensemble = str(k).zfill(2) #save ensemble number in 2 digit format
          
            #Set timestep and replace in file name
            DeltaTime = j * DeltaTimeStep
            name = repos[1][0].replace('%T', str(DeltaTime).zfill(2))
            
            #replace the ensemble number in file name
            name = name.replace('%E',ensemble)
            
            #replace the data request in file name
            if Grouping == 'met':
                name = name.replace('%query', 'lev_surface=on&var_APCP=on')
                
            if Grouping == 'tem':
                name = name.replace('%query', 'lev_2_m_above_ground=on&var_TMP')   

            #replace the source in the file name (ie. CMC NAEFS, or GFS NAEFS)
            if Source == 'NOMAD_GFS':
                name = name.replace('%S1', 'gens')
                name = name.replace('%S2', '')
                name = name.replace('%S3', 'gefs')
                
            if Source == 'NOMAD_CMC':
                name = name.replace('%S1', 'cmcens')
                name = name.replace('%S2', 'cmc_')
                name = name.replace('%S3', 'cmce')
                
            #concatenate and create wget command
            downloadname = url + name
            filename = Source + '_' + Grouping + '_' + ensemble + '_' +  str(DeltaTime).zfill(3) + '_' + timestamp + '.grib2'
            cmd = "wget -q -O " + today_repo_path + filename + " " + '"' + downloadname + '"' + " 2> NUL"
            
            #append to wget download list if file doesn't exist locally
            if not os.path.isfile(today_repo_path + filename): #if file does not exist locally
                  wget_list.append(cmd)
                  
    #now run wget with multiple threads, this speeds up download time considerably
    print '\nDownloading Files...'
    pool = multiprocessing.Pool(processes = 20)
    pool.map(os.system,wget_list)

            

    
    
def repo_pull_datamart(repos,filePath,timestamp,repo_path):
    """
    Downloads forecast data from online repository using wget
    
    Args:
        repos: the source data in a single source from the config file, see below for example
        filePath: the filepath where the scripts are run ex) Q:\WR_Ensemble_dev\A_MS\Repo\scripts
        timestamp: datestamp + start hour, this is currently the config.file date with a static start hour of '00'
        repo_path: path to store all the repo data; currently 'config_file.grib_forecast_repo'
        
        [0]   :URL                http://dd.weather.gc.ca/model_gem_regional/10km/grib2/%H/%T/                http://dd.weather.gc.ca/model_gem_global/25km/grib2/lat_lon/%H/%T/ 
        [1]   :FileName           CMC_reg_APCP_SFC_0_ps10km_%Y%m%d%H_P%T.grib2                                CMC_glb_APCP_SFC_0_latlon.24x.24_%Y%m%d%H_P%T.grib2
        [2]   :DeltaTimeStart     3                                                                           3            
        [3]   :DeltaTimeEnd       48                                                                          240        
        [4]   :DeltaTimeStep      3                                                                           3                          
        [5]   :StitchTimeStart    3                                                                           48
        [6]   :StitchTimeEnd      48                                                                          240
        [7]   :Grouping           met                                                                         met   
        [8]   :Type               GEM                                                                         GEM
        [9]   :Forecast           1                                                                           1

    """

    #build repository directory to store the date's files
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
        if not os.path.isfile(today_repo_path + name): #if file does not exist locally
          try: #download if remote file exists
              urllib2.urlopen(filename) #command to see if remote file can be opened
              os.system("wget -q -O " + today_repo_path + name + " " + filename + " 2> NUL") #use wget to actually download the file
          except urllib2.URLError as e: #do nothing if remote file doesn't exist
              print " Error: File does not exist locally or remotely"
        

      print "\n"
          
          






def grib2r2c_datamart(repos,filePath,datestamp,startHour,repo_path):
   

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
          


def grib_to_r2c_nomads(repos, r2c_repo, r2c_template, datestamp_object, repo_path):
    """
    Function to convert the files that have been downloaded via the repo_pull_nomads function
    
    
   #Example repos from config file, note substitution parameters (%X) in :FileName
   :SourceData  
   0:URL                http://nomads.ncep.noaa.gov/cgi-bin/              
   1:FileName           filter_%S1.pl?file=%S2gep%E.t%Hz.pgrb2af%T&%query&subregion=&leftlon=-98&rightlon=-88&toplat=54&bottomlat=46&dir=%2F%S3.%Y%m%d%2F00%2Fpgrb2a
   2:DeltaTimeStart     6                                                                          
   3:DeltaTimeEnd       240                                                                         
   4:DeltaTimeStep      6                                                                          
   5:StitchTimeStart    6                                                                          
   6:StitchTimeEnd      240                                                                         
   7:Grouping           tem                                                                        
   8:Type               NOMAD_GFS                                                                        
   9:Forecast           3
   10:num_ensembles     20   
    """

    #get information for source file
    Grouping = repos[7][0]
    Type = repos[8][0]
    num_ensembles = int(repos[10][0])
    
    DeltaTimeStart = int(repos[2][0])
    DeltaTimeEnd = int(repos[3][0])
    DeltaTimeStep = int(repos[4][0])
    Forecast = int(repos[9][0])
    
    today_repo_path = repo_path + "/" + datestamp_object.strftime("%Y%m%d%H") + "/"
    r2c_dest_folder = os.path.join(r2c_repo, Grouping)
    

    #for temperature and precipitation
        #for CMC and GFS
        
    #for each ensemble member (1-20)
    for i in range(1,num_ensembles+1):
        pbar = i/float(num_ensembles) * 40
        sys.stdout.write('\r')
        # the exact output you're looking for:
        sys.stdout.write("[%-40s] %d%%" % ('='*int(pbar), pbar/40*100))
        sys.stdout.flush()

        for j in range(DeltaTimeStart/DeltaTimeStep,DeltaTimeEnd/DeltaTimeStep + 1):
      
            #get file to convert
            DeltaTime = j * DeltaTimeStep
            grib_filepath = today_repo_path + Type + '_' + Grouping + '_' + "%02d" % i + '_' + "%03d" % DeltaTime + '_' + datestamp_object.strftime("%Y%m%d%H") + '.grib2'

            
            #get r2c destination filename
            r2c_dest_filename = datestamp_object.strftime("%Y%m%d") + '_' + Grouping + '_' + "%02d" % Forecast + '-' + "%02d" % i + '.r2c'
            r2c_dest_filepath = os.path.join(r2c_dest_folder,r2c_dest_filename)


            #get first file and convert to r2c
            if j == 1:
                if Grouping == 'tem':
                    pyEnSim_basics.grib_save_r2c(grib_filepath, r2c_template, r2c_dest_filepath, timestamp = datestamp_object, convert_add = -273.15)
                if Grouping == 'met':
                    pyEnSim_basics.grib_save_r2c(grib_filepath, r2c_template, r2c_dest_filepath, timestamp = datestamp_object, convert_mult = False)
            else: #for all grib files after the first file, append to existing r2c file
                if Grouping == 'tem':
                    pyEnSim_basics.grib_append_r2c(grib_filepath, r2c_template, r2c_dest_filepath, DeltaTimeStep, convert_add = -273.15)
                if Grouping == 'met':
                    pyEnSim_basics.grib_append_r2c(grib_filepath, r2c_template, r2c_dest_filepath, DeltaTimeStep, convert_mult = False)
    print '\n'


        
def query_ec_datamart_forecast(config_file):
    """
    query ec datamart to download and convert data. 
    The function looks at the ':SourceData' parameters to determine where to
    download the forecasts and how to convert them
    """
    print "Getting forecast data..."
    split_date = config_file.forecast_date.split("/")
    
    
    #initialize some useful variables
    startHour = '00'
    # now = datetime.datetime.now()
    filePath = os.path.split(os.path.abspath(__file__))[0]
    datestamp = split_date[0] + split_date[1] +split_date[2] 
    timestamp = datestamp + startHour
    
    datestamp_object = datetime.datetime.strptime(datestamp, '%Y%m%d')
    datestamp_object = datestamp_object.replace(hour = int(startHour))

    
    #Get the repository data from the config file
    getRepos = False
    repos_parent = []
    for line in open(config_file.configuration_file):
    #this for loop populates the variable 'repos_parent'
    #'repos_parent[0]' is the data for the first SourceData in the configuration file
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
    
    
    

    # Replace special characters (not %T yet) with new values
    for k in range(len(repos_parent)): #for each source data section
      for i, line in enumerate(repos_parent[k]): #for each line in a section
        for j, val in enumerate(line):#for each item in a line
          #substitue Years, Months, Days, Hours with actual dates/times from config_file.forecast_date
          repos_parent[k][i][j] = repos_parent[k][i][j].replace('%Y', split_date[0])
          repos_parent[k][i][j] = repos_parent[k][i][j].replace('%m', split_date[1])
          repos_parent[k][i][j] = repos_parent[k][i][j].replace('%d', split_date[2])
          repos_parent[k][i][j] = repos_parent[k][i][j].replace('%H', startHour)
          
    
    #Download the forecast data to directory specified in the config file
    print "Downloading Data.... \n"
    for k in range(len(repos_parent)):
      print "Downloading Forecast File(s): \n" + config_file.grib_forecast_repo + "\\" + str(timestamp)
      repo_pull_nomads(repos_parent[k], filePath, timestamp, config_file.grib_forecast_repo)
      print "\n"

      
    #first check if folders exist, create if they don't
    if not os.path.exists(filePath+"/../wxData/met"):
        os.mkdir(filePath+"/../wxData/met")
    
    if not os.path.exists(filePath+"/../wxData/tem"):
        os.mkdir(filePath+"/../wxData/tem")
        
        
    #check if r2c files exist in the working directory, only convert from grib2 to r2c if the 
    #r2c files don't already exist
    existing_metfiles = os.listdir(filePath+"/../wxData/met")
    existing_temfiles = os.listdir(filePath+"/../wxData/tem")
    pattern = str(datestamp + ".*r2c")
    
    #check if files exist in folders and proceed accordingly
    need_to_convert_met = "True"
    for file in existing_metfiles:
        if re.match(pattern, file):
          need_to_convert_met = "False"
          break
          
    need_to_convert_tem = "True"
    for file in existing_temfiles:
        if re.match(pattern, file):
          need_to_convert_tem = "False"
          break
    
    if need_to_convert_met == "False" and need_to_convert_tem == "False":
        print "Converted Files already exist in wxData/met & tem directories,"
        print "using those files, please delete if you wish to redo grib conversion"
    else:
      # convert to watflood r2c
      r2c_repo = os.path.join(filePath,"../wxData")
      r2c_template = os.path.join(filePath,"../", config_file.lib_directory,"EmptyGridLL.r2c")
           
      # print "Converting Data.... \n"
      for k in range(len(repos_parent)): #for each 'source section'
        print "Converting Forecast File(s): \n"
        grib_to_r2c_nomads(repos_parent[k], r2c_repo, r2c_template, datestamp_object, config_file.grib_forecast_repo)

        
       
    

def query_ec_datamart_hindcast(config_file):
    """

    """

    
    # capa data
    # always pull capa data

    # generate r2c from grib2
    print "Getting Precipitation Data..."
    hind_start_date = datetime.datetime.strptime(config_file.historical_start_date,"%Y/%m/%d")
    capafilename = hind_start_date.strftime("%Y%m%d_met.r2c")
    MetUpdate(config_file, 
              r2c_target_path = os.path.join(config_file.historical_capa_path,capafilename), 
              type = "CaPA", 
              RepoPath = config_file.grib_capa_repo, 
              r2c_template_path = os.path.join(config_file.repository_directory,config_file.lib_directory,"TEMPLATE_met.r2c"))
              
    #copy over to working directory          
    origin = os.path.join(config_file.historical_capa_path,capafilename)
    destination = os.path.join(config_file.model_directory_path,"radcl",capafilename)
    shutil.copyfile(origin, destination)
    
    
    
        
    # #GEM Temperature Data
    print "Getting Temperature Data..."
    hind_start_date = datetime.datetime.strptime(config_file.historical_start_date,"%Y/%m/%d")
    GEMTempsfilename = hind_start_date.strftime("%Y%m%d_tem.r2c")
    MetUpdate(config_file, 
              r2c_target_path = os.path.join(config_file.historical_GEMTemps_path,GEMTempsfilename), 
              type = "GEMTemps", 
              RepoPath = config_file.grib_GEMTemps_repo, 
              r2c_template_path = os.path.join(config_file.repository_directory,config_file.lib_directory,"TEMPLATE_tem.r2c"))
              
    #copy over to working directory          
    origin = os.path.join(config_file.historical_GEMTemps_path, GEMTempsfilename)
    destination = os.path.join(config_file.model_directory_path, "tempr", GEMTempsfilename)
    shutil.copyfile(origin, destination)
    
    #create YYYYMMDD_dif.r2c file from temperature file
    print "Calculating YYYYMMDD_dif.r2c file /n"
    cmd = [config_file.rscript_path,
          os.path.join(config_file.repository_directory,config_file.scripts_directory,"tempdiff.R"),
          os.path.join(config_file.repository_directory,config_file.scripts_directory)]
    subprocess.call(cmd,shell=True)
    
    
def Download_Datamart_ReAnalysisHindcast(config_file,type,RepoPath):
    #Initialize some useful variables
    timeVar = FrameworkLibrary.getDateTime(hours = 0) #get today at time = 0
    timestamp = timeVar.strftime("%Y%m%d%H")
    ScriptDir = config_file.scripts_directory


    #define server names
    if type == 'CaPA':
        url = 'http://dd.weather.gc.ca/analysis/precip/rdpa/grib2/polar_stereographic/06/'
        filename_nomenclature = 'CMC_RDPA_APCP-006-0700cutoff_SFC_0_ps10km_'
        
                
    else:
        raise ValueError('Source type is not defined. Only "CaPA" hindcast data can currently be downloaded')
    

    #get list of files on the server
    #http://stackoverflow.com/questions/10875215/python-urllib-downloading-contents-of-an-online-directory
    urlpath = urllib2.urlopen(url)
    server_data = urlpath.read()
    filename_pattern = re.compile('"(' + filename_nomenclature + '.+.grib2)"')
    filelist = filename_pattern.findall(server_data)
    
    
    print "Downloading grib files from DataMart..."
    #for all the files on the datamart
    for s,name in enumerate(filelist):
        try:
            if not os.path.exists(os.path.join(RepoPath, name)): #if file doesn't exist locally, then download
                os.system("wget -O " + os.path.join(RepoPath, name) + " " + url + "/" + name)
        except:
            pass
    print "All of the files have been downloaded from:\n" + url
    
    #get the timestamp of the last file
    pattern = filename_nomenclature + "(\d+)(_\d+.grib2)"

    
    m = re.match(pattern,filelist[-1])
    if m:
        lasttimestring = m.groups()[0]
        lasttimestep = datetime.datetime.strptime(lasttimestring,"%Y%m%d%H")
        
        suffix = m.groups()[1]
        grib_path_string = os.path.join(RepoPath,filename_nomenclature + "%Y%m%d%H" + suffix)


    #datetime.datetime.strptime("%Y%m%d%H"
    return lasttimestep, grib_path_string
    
    
    
def Download_Datamart_GEMHindcast(config_file,type,RepoPath):
    """
    """
    
    #Initialize some useful variables
    timeVar = FrameworkLibrary.getDateTime(hours = 0) #get today at time = 0
    timestamp = timeVar.strftime("%Y%m%d%H")
    ScriptDir = config_file.scripts_directory


    #define server/model defaults
    if type == 'GEMTemps':
        url = 'http://dd.weather.gc.ca/model_gem_regional/10km/grib2/'
        filename_nomenclature = 'CMC_reg_TMP_TGL_2_ps10km_'
        forecast_periods = [00,06,12,18] #the forecast is produced 4 times a day
        time_periods = [000,003] # want to grab these hours to stitch together
    else:
        raise ValueError('Source type is not defined. Only "GEMTemps" forecast/hindcast data can currently be downloaded')
        
        
    #the model data is only stored online for today and yesterday
    #if this changes, then you will need to modify the dates
    now = datetime.datetime.now()
    yesterday = now - datetime.timedelta(days=1)

    now_datestamp = now.strftime("%Y%m%d")
    yesterday_datestamp = yesterday.strftime("%Y%m%d")

    dates = [yesterday_datestamp,now_datestamp]
    

    #Download grib2 files from DataMart ****************************************************** 
    #While an online version exists and a local version does not download then repeat (hours 000 & 003 for all four forecasts)
    for i,startperiod in enumerate(forecast_periods):
        for j,starthour in enumerate(time_periods):
            for k,day in enumerate(dates):

                filename = filename_nomenclature + day + str(startperiod).zfill(2) +'_P' + str(starthour).zfill(3) + '.grib2'
                website = url + str(startperiod).zfill(2) + '/' + str(starthour).zfill(3) + '/' + filename
          
          
                if os.path.exists(os.path.join(RepoPath,filename)): #check if file already exists in local directory
                    lastfile = os.path.join(RepoPath,filename)
                else:
                    try: #download if remote file exists
                        urllib2.urlopen(website) #command to see if remote file can be opened
                        os.system("wget -O " + os.path.join(RepoPath,filename) + " " + website) #use wget to actually download the file
                        lastfile = os.path.join(RepoPath,filename)
                    except urllib2.URLError as e: #do nothing if remote file doesn't exist
                        pass
            
            
    print "All of the files have been downloaded from:\n" + url

    
    #get the timestamp of the last file
    pattern = filename_nomenclature + "(\d+)(_P\d+.grib2)"

    
    m = re.match(pattern,filename)
    if m:
        lasttimestring = m.groups()[0]
        lasttimestep = datetime.datetime.strptime(lasttimestring,"%Y%m%d%H")




    return lasttimestep, filename_nomenclature
    
    

def MetUpdate(config_file, r2c_target_path, type, RepoPath, r2c_template_path):
    """
    Function to update r2c files with either CaPA data or Temperature data from the EC datamart
    """
    
    if type == "CaPA":
        timestep = 6
    if type == "GEMTemps":
        timestep = 3
    
    #Check datamart repository and download any data that isn't in local repository
    if type == "CaPA":
        lastgribfiletime, grib_path_string = Download_Datamart_ReAnalysisHindcast(config_file,type,RepoPath)
    if type == "GEMTemps":
        lastgribfiletime, grib_path_string = Download_Datamart_GEMHindcast(config_file,type,RepoPath)

    
    
    #load capa template and get coordinate system
    template_r2c_object = pyEnSim_basics.load_r2c_template(r2c_template_path)

    
    #load r2c and get last frame and time
    lastindexframe, lasttimeframe = pyEnSim_basics.r2c_EndFrameData(r2c_target_path)
    
    #get the last date in the grib file repository
    print "The last frame is:    " + str(lasttimeframe)
    print "the last gribfile is: " + str(lastgribfiletime)
    print "\n"
    

    if type == "CaPA":
        #starting at the next timestep, convert specified capa grib file and append to r2c file
        current_time = lasttimeframe
        current_index = lastindexframe
        
        while(current_time < lastgribfiletime):
            current_time = current_time + datetime.timedelta(hours = timestep)
            current_index = current_index + 1
            current_gribpath = current_time.strftime(grib_path_string)
            #print current_gribpath
            
            #convert and append grib file
            pyEnSim_basics.grib_fastappend_r2c(grib_path = current_gribpath, 
                                template_r2c_object = template_r2c_object, 
                                r2cTargetFileName = r2c_target_path, 
                                frameindex = current_index, 
                                frametime = current_time, 
                                convert_mult = False, convert_add = False)
            print current_time
            
            
            

    if type == "GEMTemps":
    
        #create an ordered list of grib files to append
        current_time = lasttimeframe

        griblist = []
        while(current_time < lastgribfiletime):
            timestamp_odd = current_time.strftime("%Y%m%d%H")
            current_time = current_time + datetime.timedelta(hours = timestep)
            timestamp_even = current_time.strftime("%Y%m%d%H")
            hourstamp = current_time.strftime("%H")
            
            #get relevant grib file name; this is dependent on the hour because the forecasted temps are being used
            if int(hourstamp) in (0,6,12,18):
               gribname = os.path.join(RepoPath,grib_path_string + timestamp_even + "_P000.grib2")
               griblist.append(gribname)
           
            if int(hourstamp) in (3,9,15,21):
               gribname = os.path.join(RepoPath,grib_path_string + timestamp_odd + "_P003.grib2")
               griblist.append(gribname)
        
        
        
        #now iterate through grib list and append each file to r2c
        current_time = lasttimeframe
        current_index = lastindexframe
        
        for i, grib_path in enumerate(griblist):
            current_index = current_index + 1
            current_time = current_time + datetime.timedelta(hours = timestep)
            #convert and append grib file
            pyEnSim_basics.grib_fastappend_r2c(grib_path = grib_path, 
                                template_r2c_object = template_r2c_object, 
                                r2cTargetFileName = r2c_target_path, 
                                frameindex = current_index, 
                                frametime = current_time, 
                                convert_mult = False, convert_add = -273.15)
        


