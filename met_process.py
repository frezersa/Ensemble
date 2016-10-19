"""
Module to pre process meterological data from the:
    EC datamart - https://weather.gc.ca/grib/index_e.html
    NOMADS - http://nomads.ncep.noaa.gov/cgi-bin/
Relies heavily on the pyEnSim_basics module to convert grib files to r2c files
"""

#import standard modules
import os
import datetime
import sys
import multiprocessing
import subprocess
import urllib2
import re
import shutil

#import custom modules
import FrameworkLibrary 
import pyEnSim_basics
import pyEnSim.pyEnSim as pyEnSim

 
def repo_pull_nomads(repos, filePath, timestamp, repo_path):
    """
    Downloads forecast data from NOMADS repository using wget
    
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

    Returns:
        NULL - downloads grib files from online repository
    """
    
    #build repository directory to store the date's files
    today_repo_path = repo_path + "/" + timestamp + "/"
    FrameworkLibrary.build_dir(today_repo_path)

    #get arguments from repos, we assume that 2 NOMADS sources won't be stitched together 
    #(as we do with the datamart GEM regional and global model), hence only grab the first string (ie. repos[*][0])
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
    print '\nDownloading Files... \n'
    pool = multiprocessing.Pool(processes = 20)
    pool.map(os.system,wget_list)

            

    
    
def repo_pull_datamart(repos,filePath,timestamp,repo_path):
    """
    Downloads forecast data from EC datamart repository using wget
    http://dd.weather.gc.ca/
    
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

    Returns:
        NULL - downloads grib files from online repository
    """

    #build repository directory to store the date's files
    today_repo_path = repo_path + "/" + timestamp + "/"
    FrameworkLibrary.build_dir(today_repo_path)

    #for each of the 'series' that are being stitched together (typically 1 or 2)
    for i, url in enumerate(repos[0]): 
      DeltaTimeStart = int(repos[2][i])
      DeltaTimeEnd = int(repos[3][i])
      DeltaTimeStep = int(repos[4][i])
      
      #loop through the time series
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
          
          



def grib2r2c_datamart(repos, wx_repo, r2c_template, datestamp_object, grib_repo):
    """
    Function to process the EC datamart grib files (both deterministic and ensemble)
    
    Args:
        repos: 
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
        
        wx_repo: wxdata folder path
        r2c_template: path to r2c template
        datestamp_object: forecast date in the datetime class
        grib_repo: repository where grib data is downloaded and stored
        
    Returns:
        NULL - but creates r2c files from grib files
    """

    #get initial info from repos
    Stitches = len(repos[0])
    Grouping = repos[7][0]
    Type = repos[8][0]
    num_ensembles = int(repos[10][0])
    
    DeltaTimeStart = int(repos[2][0])
    DeltaTimeEnd = int(repos[3][0])
    Forecast = int(repos[9][0])
    
    #set folder paths
    today_grib_repo = os.path.join(grib_repo,datestamp_object.strftime("%Y%m%d%H"))
    r2c_dest_folder = os.path.join(wx_repo, Grouping)
    
    #Set the number of r2c files to produce based on user defined 'num_ensembles' arg from repos
    #note that EC datamart structure has the ensembles embedded as multiple 'children' in each grib file
    #the processing of these 'children' is done within the pyEnSim_basics.grib_save_r2c and 
    #pyEnSim_basics.grib_fastappend_r2c functions
    frame_index = 0
    if num_ensembles > 1:
        ensemble = num_ensembles
    else:
        ensemble = False
        
    #for each of the 'series' that are being stitched together (typically 1 or 2)
    for i in range(0,Stitches):

    
        StitchTimeStart = int(repos[5][i])
        StitchTimeEnd = int(repos[6][i])
        DeltaTimeStep = int(repos[4][i])
        
        print "Converting Hours: " + str(StitchTimeStart) + " to " + str(StitchTimeEnd)
        #loop through each timestep
        for j in range(StitchTimeStart/DeltaTimeStep,StitchTimeEnd/DeltaTimeStep+1):
            
            pbar = j/float(StitchTimeEnd/DeltaTimeStep) * 40
            sys.stdout.write('\r')
            # the exact output you're looking for:
            sys.stdout.write("[%-40s] %d%%" % ('='*int(pbar), pbar/40*100))
            sys.stdout.flush() 
        
            frame_index = frame_index + 1
            
            #set deltatime so that frame timestamp can be properly labelled
            if j == 1:
                DeltaTime = StitchTimeStart
            else:
                DeltaTime = DeltaTime + DeltaTimeStep

            #end loop if we've reached the end
            if DeltaTime > StitchTimeEnd:
                break

            #get first file and convert to r2c
            name = repos[1][i].replace('%T', str(DeltaTime).zfill(3)) #%Y%m%d%H have already been replaced in query_meteorological_forecast()
            grib_filepath = os.path.join(today_grib_repo,name)

            oldname = repos[1][i].replace('%T', str(DeltaTime-DeltaTimeStep).zfill(3)) #%Y%m%d%H have already been replaced in query_meteorological_forecast()
            oldgrib_filepath = os.path.join(today_grib_repo,oldname)

            
            #get r2c destination filename
            r2c_dest_filename = datestamp_object.strftime("%Y%m%d") + '_' + Grouping + '_' + "%02d" % Forecast + '-01.r2c'
            r2c_dest_filepath = os.path.join(r2c_dest_folder,r2c_dest_filename)
            
            r2c_template_object = pyEnSim_basics.load_r2c_template(r2c_template)
            frame_time = datestamp_object + datetime.timedelta(hours=int(DeltaTime))
            
            
            if Grouping == "tem":
                if j == 1:
                    #if this is the first pass, create the r2c file(s)
                    pyEnSim_basics.grib_save_r2c(grib_filepath, r2c_template, r2c_dest_filepath, timestamp = datestamp_object, convert_add = -273.15, ensemble = ensemble)
                else:
                    #append grib data to existing r2c file(s) on all other passes
                    pyEnSim_basics.grib_fastappend_r2c(grib_filepath, r2c_template_object, r2c_dest_filepath, frame_index, frame_time, convert_add = -273.15, ensemble = ensemble)
                    

            if Grouping == "met":
                if j == 1:
                    pyEnSim_basics.grib_save_r2c(grib_filepath, r2c_template, r2c_dest_filepath, timestamp = datestamp_object, ensemble = ensemble)
                else:
                    pyEnSim_basics.grib_fastappend_r2c(grib_filepath, r2c_template_object, r2c_dest_filepath, frame_index, frame_time, grib_previous = oldgrib_filepath, ensemble = ensemble)

        print "\n"
          


def grib_to_r2c_nomads(repos, r2c_repo, r2c_template, datestamp_object, grib_repo):
    """
    Function to convert the files that have been downloaded via the repo_pull_nomads function
    Note that the ensemble files are handled differently than the EC datamart ensemble files.
    NOMADS stores 1 single ensemble in 1 single grib file. There are no 'children' as in the datamart.
    
    Args:
        repos:
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
       
        wx_repo: wxdata folder path
        r2c_template: path to r2c template
        datestamp_object: forecast date in the datetime class
        grib_repo: repository where grib data is downloaded and stored
        
    Returns:
        NULL - but converts grib files to r2c
    """

    #get information for source file
    Grouping = repos[7][0]
    Type = repos[8][0]
    num_ensembles = int(repos[10][0])
    
    DeltaTimeStart = int(repos[2][0])
    DeltaTimeEnd = int(repos[3][0])
    DeltaTimeStep = int(repos[4][0])
    Forecast = int(repos[9][0])
    
    today_grib_repo = grib_repo + "/" + datestamp_object.strftime("%Y%m%d%H") + "/"
    r2c_dest_folder = os.path.join(r2c_repo, Grouping)
    
    r2c_template_object = pyEnSim_basics.load_r2c_template(r2c_template)
    

    print "Converting Hours: " + str(DeltaTimeStart) + " to " + str(DeltaTimeEnd)
    #for each ensemble member (1-20)
    for i in range(1,num_ensembles+1):
        pbar = i/float(num_ensembles) * 40
        sys.stdout.write('\r')
        # the exact output you're looking for:
        sys.stdout.write("[%-40s] %d%%" % ('='*int(pbar), pbar/40*100))
        sys.stdout.flush()

        #for each timestep
        for j in range(DeltaTimeStart/DeltaTimeStep,DeltaTimeEnd/DeltaTimeStep + 1):
      
            #get file to convert
            DeltaTime = j * DeltaTimeStep
            TimeStamp = datestamp_object + datetime.timedelta(hours = (DeltaTime-DeltaTimeStep))
            grib_filepath = today_grib_repo + Type + '_' + Grouping + '_' + "%02d" % i + '_' + "%03d" % DeltaTime + '_' + datestamp_object.strftime("%Y%m%d%H") + '.grib2'

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
                    pyEnSim_basics.grib_fastappend_r2c(grib_filepath, r2c_template_object, r2c_dest_filepath, frameindex = j, frametime = TimeStamp, convert_add = -273.15)
                if Grouping == 'met':
                    pyEnSim_basics.grib_fastappend_r2c(grib_filepath, r2c_template_object, r2c_dest_filepath, frameindex = j, frametime = TimeStamp, convert_mult = False)
    print '\n'


        
def query_meteorological_forecast(config_file):
    """
    Query EC datamart and/or NOMADS to download and convert data. 
    The function looks at the ':SourceData' parameters to determine where to
    download the forecasts and how to convert them
    
    Args:
        config_file: see class ConfigParse()
    Returns:
        NULL - but gets and processes meteorological forecast files
    """
    print "Getting forecast data..."

    #initialize time variables
    startHour = '00'
    datestamp_object = datetime.datetime.strptime(config_file.forecast_date, '%Y/%m/%d')
    datestamp_object = datestamp_object.replace(hour = int(startHour))
    timestamp = datestamp_object.strftime("%Y%m%d%H")
    datestamp = datestamp_object.strftime("%Y%m%d")

    #get path
    repo_path = config_file.repository_directory
    wx_path = os.path.join(repo_path,"wxData")

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
          repos_parent[k][i][j] = repos_parent[k][i][j].replace('%Y', "%04d" % datestamp_object.year)
          repos_parent[k][i][j] = repos_parent[k][i][j].replace('%m', "%02d" % datestamp_object.month)
          repos_parent[k][i][j] = repos_parent[k][i][j].replace('%d', "%02d" % datestamp_object.day)
          repos_parent[k][i][j] = repos_parent[k][i][j].replace('%H', startHour)
          
    
    #Download the forecast data to directory specified in the config file
    print "Downloading Data.... \n"
    for k in range(len(repos_parent)):
    
      Type = repos_parent[k][8][0]
      Grouping = repos_parent[k][7][0]
      print Type + " - " + Grouping
      
      if "NOMAD" in Type: #if NOMADS
        repo_pull_nomads(repos_parent[k], wx_path, timestamp, config_file.grib_forecast_repo)
      else: #else assume EC datamart
        repo_pull_datamart(repos_parent[k], wx_path, timestamp, config_file.grib_forecast_repo)
      

    # Now process the downloaded files into WATFLOOD format************************
    
    #first check if folders exist, create if they don't
    if not os.path.exists(os.path.join(wx_path,"met")):
        os.mkdir(os.path.join(wx_path,"met"))
    
    if not os.path.exists(os.path.join(wx_path,"tem")):
        os.mkdir(os.path.join(wx_path,"tem"))
        
        
    #check if r2c files exist in the working directory, only convert from grib2 to r2c if the 
    #r2c files don't already exist
    existing_metfiles = os.listdir(os.path.join(wx_path,"met"))
    existing_temfiles = os.listdir(os.path.join(wx_path,"tem"))
    pattern = str(datestamp + ".*r2c")
    
    #check if files exist in folders and proceed accordingly
    need_to_convert_met = "True"
    for file in existing_metfiles:
        if re.search(pattern, file):
          need_to_convert_met = "False"
          break
          
    need_to_convert_tem = "True"
    for file in existing_temfiles:
        if re.search(pattern, file):
          need_to_convert_tem = "False"
          break
    
    if need_to_convert_met == "False" and need_to_convert_tem == "False":
        print "Converted Files already exist in wxData/met & tem directories,"
        print "using those files, please delete if you wish to redo grib conversion"
    else:
      # convert to watflood r2c
      r2c_template = os.path.join(repo_path,config_file.lib_directory,"EmptyGridLL.r2c")
           
      print "Converting Data.... \n"
      for k in range(len(repos_parent)): #for each 'source section'
      
        Type = repos_parent[k][8][0]
        Grouping = repos_parent[k][7][0]
        print Type + " - " + Grouping

        if "NOMAD" in Type: #if in NOMADS format
            grib_to_r2c_nomads(repos_parent[k], wx_path, r2c_template, datestamp_object, config_file.grib_forecast_repo)
        else: #else assume in EC datamart format
            grib2r2c_datamart(repos_parent[k], wx_path, r2c_template, datestamp_object, config_file.grib_forecast_repo)

       
    

def Download_Datamart_ReAnalysisHindcast(config_file, type, RepoPath):
    """
    Downloads reanalysis data from the EC datamart, converts and appends it to existing data.
    This is meant to update hindcast meteorological data up to the current date before the hindcast is run.
    It is currently only used for CaPA data.
    
    Args:
        config_file: see class ConfigParse()
        type: string to determine type of ReAnalysis Data; currently CaPA is the only reanalysis that exists
        RepoPath: directory where the reanalysis hindcast r2c file is stored and the reanalysis grib files are stored
    Returns:
        NULL - but downloads, converts and appends reanalysis data to r2c files
    """
    
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

    m = re.search(pattern,filelist[-1]) #only look at the last file in the list
    if m:
        lasttimestring = m.groups()[0]
        lasttimestep = datetime.datetime.strptime(lasttimestring,"%Y%m%d%H")
        
        suffix = m.groups()[1]
        grib_path_string = os.path.join(RepoPath,filename_nomenclature + "%Y%m%d%H" + suffix)

    #return values if the pattern was found, this will give an error if the pattern doesn't match
    #this error is intentional because the user must troubleshoot it if this occurs
    return lasttimestep, grib_path_string
    
    
    
def Download_Datamart_GEMHindcast(config_file, type, RepoPath):
    """
    Downloads forecast data from the EC datamart, converts and appends it to existing data.
    This is meant to update hindcast meteorological data up to the current date before the hindcast is run.
    It is currently only used for temperature data. Currently the best way to get gridded temperature data
    with good temporal resolution is to use the prior days' forecast.
    
    Args:
        config_file: see class ConfigParse()
        type: string to determine type of ReAnalysis Data; currently CaPA is the only reanalysis that exists
        RepoPath: directory where the reanalysis hindcast r2c file is stored and the reanalysis grib files are stored
    Returns:
        NULL - but downloads, converts and appends reanalysis data to r2c files
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
    for k,day in enumerate(dates):
        for i,startperiod in enumerate(forecast_periods):
            for j,starthour in enumerate(time_periods):
            
                filename = filename_nomenclature + day + str(startperiod).zfill(2) +'_P' + str(starthour).zfill(3) + '.grib2'  
                website = url + str(startperiod).zfill(2) + '/' + str(starthour).zfill(3) + '/' + filename
          
                if os.path.exists(os.path.join(RepoPath,filename)): #check if file already exists in local directory
                    lastfile = filename

                else:
                    try: #download if remote file exists
                        urllib2.urlopen(website) #command to see if remote file can be opened
                        os.system("wget -O " + os.path.join(RepoPath,filename) + " " + website) #use wget to actually download the file
                        lastfile = os.path.join(RepoPath,filename)
                    except urllib2.URLError as e: #do nothing if remote file doesn't exist
                        pass
            
            
    print "All of the files have been downloaded from:\n" + url

    
    #get the timestamp of the last file
    pattern = filename_nomenclature + "(\d+)_P(\d+).grib2"

    m = re.search(pattern,lastfile)
    if m:
        lasttimestring = m.groups()[0]
        forecast_hour = int(m.groups()[1])
        lasttimestep = datetime.datetime.strptime(lasttimestring,"%Y%m%d%H") + datetime.timedelta(hours=forecast_hour)

    #return values if the pattern was found, this will give an error if the pattern doesn't match
    #this error is intentional because the user must troubleshoot it if this occurs
    return lasttimestep, filename_nomenclature
    
    

def MetUpdate(config_file, r2c_target_path, type, RepoPath, r2c_template_path):
    """
    Function to update r2c files with either CaPA data or Temperature data from the EC datamart
    
    Args:
        config_file: see class ConfigParse()
        r2c_target_path: path to the r2c file that is being updated
        type: string; currently either 'CaPA' or 'GEMTemps'
        RepoPath: path to the directory where the downloaded grib files are stored
        r2c_template_path: path to a r2c template that has the same format as the r2c_target_path, this is used because it is quicker to load
    Returns:
        NULL: 
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
            
            #convert and append grib file
            pyEnSim_basics.grib_fastappend_r2c(grib_path = current_gribpath, 
                                template_r2c_object = template_r2c_object, 
                                r2cTargetFilePath = r2c_target_path, 
                                frameindex = current_index, 
                                frametime = current_time, 
                                convert_mult = False, convert_add = False, ensemble = False)

            
            
            

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
                                r2cTargetFilePath = r2c_target_path, 
                                frameindex = current_index, 
                                frametime = current_time, 
                                convert_mult = False, convert_add = -273.15, ensemble = False)
        


def query_ec_datamart_hindcast(config_file):
    """
    Function to download temperature (GEM regional forecast) and precipitation (CaPA) grib
    files from the EC datamart, then convert and append them to the existing hindcast r2c files.
    
    These files are updated with the latest data from the datamart, regardless of what time the forecast is set for
    (ie. r2cs will still update if re-running a forecast from a week ago)
    
    Args: 
        config_file: see class ConfigParse

    """
    #First do CaPA data
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
    
      
      
    #Next do GEM Temperature Data
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
          os.path.join(config_file.repository_directory,config_file.scripts_directory,config_file.r_script_tempdiff),
          os.path.join(config_file.repository_directory,config_file.scripts_directory),
          os.path.join(config_file.model_directory_path, "tempr")]
    subprocess.call(cmd,shell=True)
    
    
    