'''
Library of functions that are called by LWCB_Framework_Run_Model.py
'''

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
import multiprocessing
# NRC pyEnSim. must be installed prior to use.
import pyEnSim.pyEnSim as pyEnSim 


    

def setup_members(config_file,member):
    """
    Function to clean up the working 'Repo' directory of the specfied member and
    copy and modify the reservoir release files

    Args:
    config_file: see class ConfigParse
    member: name of hydrological ensemble member
    
    Returns:
    Null
    """
    
    #clean up the member repository
    member_repository = os.path.join(os.path.dirname(os.path.dirname(config_file.repository_directory)), member,"Repo")
    clean_up(member_repository)
        
    #copy the reservoir release files from the 'mothership' and modify the coefficients as required
    CopyModResrl(os.path.join(config_file.repository_directory,"wpegr","resrl"),
                 os.path.join(member_repository,"wpegr","resrl"),
                 os.path.join(member_repository,"lib","template_rel.tb0"))

                 
def copy_memberevents(config_file,member):
    """
    Function to Copy event files to different member directory and 
    changes paths of specified files back to the 'mothership' directory

    Args:
    config_file: see class ConfigParse
    member: name of hydrological ensemble member
    
    Returns:
    NULL
    """
    
    member_repository = os.path.join(os.path.dirname(os.path.dirname(config_file.repository_directory)), member,"Repo")
    
    CopyModEvent(os.path.join(config_file.repository_directory,"wpegr","event"),
                 os.path.join(member_repository,"wpegr","event"),
                 "NA")
                 
                 
def execute_and_plot_spinup(input):
    """
    Function to execute and plot WATFLOOD spinup; then copy results from the working 'Repo' directory
    to the 'Repo_spinup' directory.
    
    This is used in conjunction with the multiprocessing.Pool() function, which it requires a single input.
    The multiple input requirement is bypassed by joining them in a tuple and parsing them inside the function
    
    Args:
    input: list of 3 arguments
            input[0]: config_file - see class ConfigParse
            input[1]: member directory - specifies which hydrogolical member of ensemble is used
            
    Returns:
    NULL
    """
    
    #parse input
    config_file = input[0]
    member_directory = input[1]
    
    #execute spinup
    execute_watflood(config_file,member_directory)

    #plot results
    generate_analysis_graphs(config_file,
                            start_date = config_file.spinup_start_date,
                            member_directory = member_directory)
  
    #copy results
    print member_directory
    if os.path.exists(os.path.join(os.path.dirname(member_directory), "Repo_spinup")):
        shutil.rmtree(os.path.join(os.path.dirname(member_directory), "Repo_spinup"), onerror=onerror)
    shutil.copytree(os.path.join(os.path.dirname(member_directory), "Repo"),
                                os.path.join(os.path.dirname(member_directory), "Repo_spinup"),
                                ignore = shutil.ignore_patterns("wxData", "bin"))
                                
                                
                                
def execute_and_plot_hindcast(input):
    """
    Function to execute and plot WATFLOOD hindcast; then copy results from the working 'Repo' directory
    to the 'Repo_hindcast' directory.
    
    This is used in conjunction with the multiprocessing.Pool() function, which it requires a single input.
    The multiple input requirement is bypassed by joining them in a tuple and parsing them inside the function
    
    Args:
    input: list of 3 arguments
            input[0]: config_file - see class ConfigParse
            input[1]: member directory - specifies which hydrogolical member of ensemble is used
            
    Returns:
    NULL
    """
    
    #parse inpute
    config_file = input[0]
    member_directory = input[1]
    
    #execute hindcast
    execute_watflood(config_file,member_directory)

    
    #plot results
    generate_analysis_graphs(config_file,
                            start_date = config_file.historical_start_date,
                            member_directory = member_directory)
  
    #copy results
    print member_directory
    if os.path.exists(os.path.join(os.path.dirname(member_directory), "Repo_hindcast")):
        shutil.rmtree(os.path.join(os.path.dirname(member_directory), "Repo_hindcast"), onerror=onerror)
    shutil.copytree(os.path.join(os.path.dirname(member_directory), "Repo"),
                                os.path.join(os.path.dirname(member_directory), "Repo_hindcast"),
                                ignore = shutil.ignore_patterns("wxData", "bin"))
                                
                                
def execute_and_save_forecast(input):
    """
    Function to execute WATFLOOD forecast and rename&copy the results to a specified
    directory (this is usually the forecast directory in the working 'Repo' directory)
    
    This is used in conjunction with the multiprocessing.Pool() function, which it requires a single input.
    The multiple input requirement is bypassed by joining them in a tuple and parsing them inside the function
    
    Args:
    input: list of 3 arguments
            input[0]: config_file - see class ConfigParse
            input[1]: member directory - specifies which hydrogolical member of ensemble is used
            input[2]: metfile - specifies which meteorological ensemble member used
            
    Returns:
    NULL
    """
    
    #parse input file
    config_file = input[0]
    member_directory = input[1]
    metfile = input[2]
    
    #run watflood
    execute_watflood(config_file,member_directory)
  
    #save results to common folder
    shutil.copyfile(member_directory + "/wpegr/results/spl.csv",member_directory + "/forecast/" + "spl" + str(metfile[13:17]) + ".csv")
    shutil.copyfile(member_directory + "/wpegr/results/resin.csv",member_directory + "/forecast/" + "resin" + str(metfile[13:17]) + ".csv")
    
    
    
def analyze_and_plot_forecast(input):
    """
    Function to analyze all of the WATFLOOD forecasts and plot the ensembles;
    then copy results from the working 'Repo' directory to the 'Repo_forecast' directory.

    
    This is used in conjunction with the multiprocessing.Pool() function, which it requires a single input.
    The multiple input requirement is bypassed by joining them in a tuple and parsing them inside the function
    
    Args:
    input: list of 3 arguments
            input[0]: config_file - see class ConfigParse
            input[1]: member directory - specifies which hydrogolical member of ensemble is used
            
    Returns:
    NULL
    """
    config_file = input[0]
    member_directory = input[1]
    
    #plot results
    generate_analysis_graphs(config_file,
                            start_date = config_file.historical_start_date,
                            member_directory = member_directory,
                            resin = os.path.join(member_directory,"forecast/resin1-00.csv"),
                            spl = os.path.join(member_directory,"forecast/spl1-00.csv"),
                            spinup = os.path.join(member_directory,"../Repo_hindcast"))
    generate_ensemble_graphs(config_file,member_directory) 
  
    #copy results
    print member_directory
    if os.path.exists(os.path.join(os.path.dirname(member_directory), "Repo_forecast")):
        shutil.rmtree(os.path.join(os.path.dirname(member_directory), "Repo_forecast"), onerror=onerror)
    shutil.copytree(os.path.join(os.path.dirname(member_directory), "Repo"),
                                os.path.join(os.path.dirname(member_directory), "Repo_forecast"),
                                ignore = shutil.ignore_patterns("wxData", "bin"))
                                

  
def onerror(func, path, exc_info):
    """
    http://stackoverflow.com/questions/2656322/shutil-rmtree-fails-on-windows-with-access-is-denied
    Error handler for ``shutil.rmtree``.

    If the error is due to an access error (read only file)
    it attempts to add write permission and then retries.

    If the error is for another reason it re-raises the error.

    Usage : ``shutil.rmtree(path, onerror=onerror)``
    """
    import stat
    if not os.access(path, os.W_OK):
        # Is the error an access error ?
        os.chmod(path, stat.S_IWUSR)
        func(path)
    else:
        raise
        
        
def CopyModEvent(mothership_dir,member_dir,keywords="NA"):
    """
    Function specifically for hydrological ensemble modelling. Copies event files to different 
    member directory and changes paths of specified files back to the 'mothership' directory.
    
    Args: mothership_dir: 'event' directory of mothership
          member_dir: 'event' directory of member
          keywords: flags found in event file that need changing
          
    Returns:
    NULL
    """
    
    #get path and names of event files
    mothership_path = os.path.dirname(mothership_dir)
    mothership_files = os.listdir(mothership_dir)
    
    #copy event files from mothership to member, keep log
    member_files = []
    for file_name in mothership_files:
        full_file_name = os.path.join(mothership_dir, file_name)
        if (os.path.isfile(full_file_name)):
          shutil.copy(full_file_name, member_dir) #copy files
          member_files.append(os.path.join(member_dir,file_name)) #create list of copied files
          
    if keywords == "NA":
       keywords = ["pointsoilmoisture", "pointprecip", "pointtemps", "streamflowdatafile", "reservoirinflowfile", "diversionflowfile",
                  "snowcoursefile", "observedlakelevel", "initlakelevel", "griddedinitsnowweq", "griddedinitsoilmoisture", "griddedrainfile",
                  "griddedtemperaturefile", "griddeddailydifference"]
                  
    #Go through each new event file and change path to mothership
    for file_name in member_files:
        Infile = open(file_name, 'rb')
        table = [row.strip().split() for row in Infile]

        for i, line in enumerate(table):
            for flag in keywords:
               if flag in line[0] and mothership_path not in line[1]:
                  line[1] = os.path.join(mothership_path,line[1])
                  
        file = open(file_name,'w')
        #write file
        for i, line in enumerate(table):
            for j, val in enumerate(line):
                if j is 0:
                    file.write(str(val.ljust(40)))
                else:
                    file.write(str(val) + " ")
            file.write('\n')
            
            
def CopyModResrl(mothership_dir,member_dir,template):
    """
    Function to copy reservoir release files from the 'mothership' directory and change the 
    coefficients (ie stage discharge curve) to be specific for the member calibration.
    
    Args:
        mothership_dir: the mothership directory where the 'resrl' files are stored
                        ex) 'Q:\WR_Ensemble_dev\A_MS\Repo\wpegr\resrl'
        member_dir: the member directory where the 'resrl' files are stored
                        ex) 'Q:\WR_Ensemble_dev\51-A\Repo\wpegr\resrl'
        template: the member directory where the 'resrl' template is stored, this 
                    needs to have the same number and order of reservoirs as the mothership
                    
    Returns:
    NULL
    """

    #find all of the release files in the mothership 'resrl' directory 
    #(reservoir inflow files are stored in the same directory)
    mothership_path = os.path.dirname(mothership_dir)
    mothership_files = [s for s in os.listdir(mothership_dir) if 'rel' in s]

    #copy found files into member directory and log the records
    member_files = []
    for file_name in mothership_files:
        full_file_name = os.path.join(mothership_dir, file_name)
        if (os.path.isfile(full_file_name)):
          shutil.copy(full_file_name, member_dir) #copy files
          member_files.append(os.path.join(member_dir,file_name)) #create list of copied files

    keywords = ["coeff1","coeff2","coeff3","coeff4","coeff5"]
    
    #get template data
    template_file = open(template, 'rb')
    template_table = [row.strip().split() for row in template_file]
    template_line = []
    for flag in keywords:
        for t in template_table:
            if flag in t[0]:
                template_line.append(t) #line from template
          
    #Go through each new resrl file
    for file_name in member_files:
        Infile = open(file_name, 'rb')
        table = [row.strip().split() for row in Infile]
        
        file = open(file_name,'w')
        flag_data = "False"
        for i, line in enumerate(table):
            for newline in template_line: #check for template match
                if newline[0] in line[0]:
                    line = newline
                    
            if flag_data == "True":
                file.write("                    ")
                for j, val in enumerate(line):
                        file.write(str(val.ljust(13)))
                file.write('\n')
            else:
                 for j, val in enumerate(line):
                    if j is 0:
                        file.write(str(val.ljust(20)))
                    else:
                        file.write(str(val.ljust(13)))
                 file.write('\n')
                
            if "endHeader" in line[0]:
                flag_data = "True"
                
                
            
def parse_configuration_file(configuration_file):
    """
    parse configuration file name:value into a dict.
    used to create class ConfigParse
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
        self.ensemble_members = parameter_settings["ensemble_members"]
         
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
    
    
    

def getDateTime(hours):
    """
    gets a DateTime hours hours from midnight this morning
    
    Args:
        hours: integer, see grib2r2c function
    """
    tm = datetime.datetime.now()
    newdate = datetime.datetime(tm.year, tm.month, tm.day, 0, 0, 0)
    newdate = newdate + datetime.timedelta(hours=hours)
    return newdate

    
    

def build_dir(directory):
    """
    checks to see if a directory exists and creates it if it does not
    Args:
        build_dir: directory path
    """

    d = os.path.dirname(directory)
    if not os.path.exists(d):
        os.makedirs(d)
    
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
   :URL                http://nomads.ncep.noaa.gov/cgi-bin/              
   :FileName           filter_%S1.pl?file=%S2gep%E.t%Hz.pgrb2af%T&%query&subregion=&leftlon=-98&rightlon=-88&toplat=54&bottomlat=46&dir=%2F%S3.%Y%m%d%2F00%2Fpgrb2a
   :DeltaTimeStart     6                                                                          
   :DeltaTimeEnd       240                                                                         
   :DeltaTimeStep      6                                                                          
   :StitchTimeStart    6                                                                          
   :StitchTimeEnd      240                                                                         
   :Grouping           tem                                                                        
   :Type               NOMAD_GFS                                                                        
   :Forecast           3                                                                          
:EndSourceData

    """
    #build repository directory to store the date's files
    today_repo_path = repo_path + "/" + timestamp + "/"
    build_dir(today_repo_path)
    

    

    
    for i, url in enumerate(repos[0]): 
      DeltaTimeStart = int(repos[2][i])
      DeltaTimeEnd = int(repos[3][i])
      DeltaTimeStep = int(repos[4][i])
      Source =  repos[8][i]
      Grouping = repos[7][i]
      wget_list = []
      
      print 'building list of files for download'
      for k in range(1,20): #for each ensemble member
        #set progress bar
        pbar = k/float(19) * 40
        sys.stdout.write('\r')
        # the exact output you're looking for:
        sys.stdout.write("[%-40s] %d%%" % ('='*int(pbar), pbar/40*100))
        sys.stdout.flush()
      
        for j in range(DeltaTimeStart/DeltaTimeStep,DeltaTimeEnd/DeltaTimeStep + 1): #for each timestep
        
            ensemble = str(k).zfill(2) #save ensemble number in 2 digit format
          
            #Set timestep and replace in file name
            DeltaTime = j * DeltaTimeStep
            name = repos[1][i].replace('%T', str(DeltaTime).zfill(2))
            
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
          
          
def grib2r2c_nomads(repos, filePath, datestamp, startHour, repo_path):
    """
    Function to conver the files that have been downloaded via the repo_pull_nomads function
    """

    #get information for source file
    #for temperature and precipitation
        #for CMC and GFS
            #for each ensemble member (1-20)
                #get first file and conver to r2c
                #for each of the next timesteps
                    #get file and convert&append to existing r2c
                #save final r2c file to correct path







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
      print "Downloading Forecast File(s): \n" + str(repos_parent[k][1]) 
      repo_pull_nomads(repos_parent[k], filePath,timestamp, config_file.grib_forecast_repo)
      print "\n"

    #check if r2c files exist in the working directory, only convert from grib2 to r2c if the 
    #r2c files don't already exist
    existing_metfiles = os.listdir(filePath+"/../wxData/met")
    existing_temfiles = os.listdir(filePath+"/../wxData/tem")
    pattern = str(datestamp + ".*r2c")
    
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
      # first remove old r2c files from temporary directory
      shutil.rmtree(filePath+"/../wxData/met")
      shutil.rmtree(filePath+"/../wxData/tem")
      os.mkdir(filePath+"/../wxData/met")
      os.mkdir(filePath+"/../wxData/tem")

      
      # print "Converting Data.... \n"
      for k in range(len(repos_parent)):
        print "Converting Forecast File(s): \n" + str(repos_parent[k][1]) 
        grib2r2c_nomads(repos_parent[k], filePath, datestamp, startHour, config_file.grib_forecast_repo)
        
       
    

def query_ec_datamart_hindcast(config_file):
    """

    """

    
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
      


    

def generate_run_event_files_forecast(config_file,members):
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
   
    
    for i,metfile in enumerate(met_list):
      print "Running Scenario: " + metfile[13:17]
      # generate the forecast event file
      
      #assign the temperature file name, if it doesn't exist, use the most recent working temperature file
      try:
        tem_list[i]
      except IndexError:
        print "using default temp file \n"
      else:
        new_temperature_file = tem_list[i]
        new_tempdiff_file = dif_list[i]
        print "sure, it was defined."
      cmd = ["python",os.path.join(config_file.repository_directory,config_file.scripts_directory,"EventGenerator.py"),"-FS",config_file.forecast_date,
          "-f",":resumflg","y",
          "-f",":tbcflg","n",
          "-f",":griddedrainfile","radcl\\" + metfile, 
          "-f",":griddedtemperaturefile","tempr\\" + new_temperature_file,
          "-f",":griddeddailydifference","tempr\\" + new_tempdiff_file,
          "-fd","1900/01/01","-f",":noeventstofollow","0",
          config_file.historical_start_date]
      subprocess.call(cmd,shell=True)
    
      #copy to other members
      for i in members:
        copy_memberevents(config_file,i)

      #execute parallel program to loop through each met forecast and run watflood
      input = [[config_file,config_file.repository_directory,metfile]] #MotherShip input
      for j,member in enumerate(members): #member input
          member_repository = os.path.join(os.path.dirname(os.path.dirname(config_file.repository_directory)), member,"Repo")
          input.append([config_file,member_repository,metfile])
          
      pool = multiprocessing.Pool(processes = len(members) + 1)
      pool.map(execute_and_save_forecast,input)
        

def generate_forecast_streamflow_file():
    """
    sets stations to -1 to only get natural flows from reservoirs.
    
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




def generate_forecast_files(config_file):
    """
    generates following 4 forecast files. streamflow, reserviour release, resevoir inflows & diversions. following :endheader tag, 10 days of rows populated
    with either -1 or 0. 
    """
    
    print "Generating streamflow, reservoir and diversion forecast files..."
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

    

def execute_watflood(config_file,calibration_directory):
    """
    execute watflood model, current directory must be model directory.
    """

    # must change to root of model directory
    os.chdir(os.path.join(calibration_directory,"wpegr"))  
    # print calibration_directory

    
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
            "-f",":noeventstofollow","0",event_start,
            "-f",":tbcflg","y"] #1900 is a dummy year that needs to be entered for the EventGenerator to work
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



    
def clean_up(repository_directory,tem="True",met="True"):
    """
    removes files from folders prior to execution of framework.
    example repository_directory is "C:\WR_Ensemble\A_MS\Repo", 
    which contains 'wpegr, diagnostic, wxdata, etc'
    """
    print "Cleaning up old files..."
    

    directories = ["diver","event","level","moist","radcl","raing","resrl","results","snow1","strfw","tempg","tempr"]
        
    # delete folders in model directory. removes all files.
    for i in directories:
        if os.path.exists(os.path.join(repository_directory,"wpegr",i)):
          shutil.rmtree(os.path.join(repository_directory,"wpegr",i))
          
    # create blank directories in model directory
    for i in directories:
        os.mkdir(os.path.join(repository_directory,"wpegr",i))
    
    # remove forecast weather data r2c's
    # files from met/ & /tem dirs
    if tem == "True":
      path = os.path.join(repository_directory,"wxData","tem","*.*")
      files = glob.glob(path)
      for i in files:
          os.remove(i)
    if met == "True":
      path = os.path.join(repository_directory,"wxData","met","*.*")
      files = glob.glob(path)
      for i in files:
          os.remove(i)
    
    # remove r generate analysis png's
    path = os.path.join(repository_directory,"diagnostic","*.*")
    files = glob.glob(path)
    for i in files:
        os.remove(i)
        
    # remove forecast csvs
    path = os.path.join(repository_directory,"forecast","*.*")
    files = glob.glob(path)
    for i in files:
        os.remove(i)
        
    

    

    
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
                              spinup="False",
                              member_directory = "NA"):
    """
    generates R daily graphics based on output of model resin & spl png files. output to /diagnostic folder
    """
    print "Generating Deterministic inflow and streamflow plots..."
    if member_directory == "NA":
        member_directory = os.path.dirname(config_file.model_directory)
    
    #= resin comparison graphic    
    # convert historical date from yyyy/mm/dd to yyyy-mm-dd
    tmp = config_file.spinup_start_date.split("/")
    if start_date == "NA":
      start_date = "%s-%s-%s" %(tmp[0],tmp[1],tmp[2])

    # resin.csv
    if resin == "NA":
      resin = os.path.join(member_directory,"wpegr","results","resin.csv")
    spinup_resin = spinup
    
    if not spinup =="False":
      spinup_resin = os.path.join(spinup,"wpegr","results","resin.csv")
      
    cmd = [config_file.rscript_path,
          os.path.join(config_file.r_script_directory, config_file.r_script_analysis_resin),
          config_file.r_script_directory,
          os.path.join(member_directory,"diagnostic"),
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
      spl = os.path.join(member_directory,"wpegr","results","spl.csv")
    spinup_spl = spinup
    if not spinup =="False":
      spinup_spl = os.path.join(spinup,"wpegr","results","spl.csv")
    cmd = [config_file.rscript_path,
          os.path.join(config_file.r_script_directory,config_file.r_script_analysis_spl),
          config_file.r_script_directory,
          os.path.join(member_directory,"diagnostic"),
          spl,
          start_date,
          end_date,spinup_spl]
    subprocess.call(cmd,shell=True)
    
    
    
def generate_ensemble_graphs(config_file,member_directory):
    """
    generates R daily graphics based on output of model resin & spl png files. output to /diagnostic folder
    """
    
    print "generating probablistic data"
    cmd = [config_file.rscript_path,
          os.path.join(config_file.r_script_directory,config_file.r_script_ensemblegraphs),
          os.path.join(member_directory,"scripts")]
    #"rscript C:\Ensemble_Framework\EC_Operational_Framework\Model_Repository\scripts\Ensemble_plot.R"
    subprocess.call(cmd,shell=True)
    

    

def generate_meteorlogical_graphs(config_file):
    """
    generates R daily graphics based on output of model resin & spl png files. output to /diagnostic folder
    """
    

    print "Generating meteorlogical plots..."
    tmp = config_file.forecast_date.split("/")
    date_str = "%s%s%s" % (tmp[0],tmp[1],tmp[2])
    met_str_forecast = os.path.join(config_file.model_directory, "radcl", date_str + "_met_1-00.r2c")
    tem_str_forecast = os.path.join(config_file.model_directory, "tempr", date_str + "_tem_1-00.r2c")
    
    tmp = config_file.historical_start_date.split("/")
    start_date = "%s%s%s" %(tmp[0],tmp[1],tmp[2])
    source_dir = os.path.join(os.path.dirname(config_file.repository_directory), "Repo_hindcast")
    met_str_hindcast = os.path.join(source_dir, "wpegr", "radcl", start_date + "_met.r2c")
 
    cmd = [config_file.rscript_path, os.path.join(config_file.r_script_directory, config_file.r_script_forecast),
            config_file.r_script_directory,
            config_file.r_graphics_directory,
            met_str_forecast,
            tem_str_forecast,
            met_str_hindcast,
            config_file.forecast_date]
    subprocess.call(cmd,shell=True)
    
      


def copy_resume(config_file,source_dir,member_path="NA"): #source dir is the name of the folder where the results come from (ex. Model_Repository_Spinup)
    #get full path of source directories
    print "Copying resume files from " + source_dir + "...." + "\n"
    
    if member_path == "NA":
      member_path = os.path.dirname(config_file.repository_directory)
    
    #delete \wpegr\flowinit.r2c,soilinit.r2c,resume.txt if exists
    resume_files = ["flow_init.r2c","soil_init.r2c","resume.txt","lake_level_init.pt2"]
    del_items = []
    make_items = []
    
    for i in resume_files:
      del_path = os.path.join(member_path,"Repo","wpegr",i)
      del_items.append(del_path)
      
      make_path = os.path.join(member_path,source_dir,"wpegr",i)
      make_items.append(make_path)
        
    # delete \wpegr\level\20140101_ill.pt2 in dest directory if exists
    tmp = config_file.historical_start_date.split("/")
    ill_file = "%s%s%s" %(tmp[0],tmp[1],tmp[2]) + "_ill.pt2"
    ill_path = os.path.join(source_dir,"wpegr","level",ill_file)
    del_items.append(ill_path)
    
    for d in del_items: 
      if os.path.exists(d):
        os.remove(d)
        
    #copy \wpegr\flowinit.r2c,soilinit.r2c,resume.txt to dest directory from source directory
    for m in range(len(make_items)):
      shutil.copyfile(make_items[m],del_items[m])

    print "\n"
    
    
    
def generate_dss(hecdss_vue_path,r_script_directory,hec_writer_script):
    inputfile = os.path.join(r_script_directory,"../diagnostic/Prob_forecast.csv")
    outputfile = os.path.join(r_script_directory,"../diagnostic/HECfile.dss")
    
    if not os.path.isfile(inputfile):
      print "Error: the input file: '" + str(inputfile) + "' does not exist \n and hence a DSS file cannot be created. Please ensure file 'Prob_forecast.csv' exists in the diagnostic directory"

    cmd = [hecdss_vue_path,os.path.join(r_script_directory,hec_writer_script),outputfile,inputfile]
    #cmd = ["C:\Program Files (x86)\HEC\HEC-DSSVue\HEC-DSSVue.exe","C:\Test_Framework\EC_Operational_Framework\Model_Repository\scripts\Writer_hec_dss_prob.py","C:/Test_Framework/EC_Operational_Framework/Model_Repository/diagnostic/HECfile.dss","C:/Test_Framework/EC_Operational_Framework/Model_Repository/diagnostic/Prob_forecast.csv"]
    
    subprocess.call(cmd,shell=True)

    

