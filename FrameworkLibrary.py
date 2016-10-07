"""
Library of functions that are called by LWCB_Framework_Run_Model.py
"""

#import standard modules
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
import tempfile

# NRC pyEnSim. must be installed prior to use.
import pyEnSim.pyEnSim as pyEnSim 

#import custom framework modules
import pyEnSim_basics
import met_process
import post_process
import pre_process


    

    
def clean_up(config_file, tem = True, met = True):
    """
    Removes files from folders prior to execution of framework.

    Args:
        repository_directory: directory which should be cleaned
            example is "C:\WR_Ensemble\A_MS\Repo", which contains 
            'wpegr, diagnostic, wxdata, etc'
    
    Returns:
        NULL
    """
    print "Cleaning up old files..."
    

    directories = ["diver","event","level","moist","radcl","raing","resrl","results","snow1","strfw","tempg","tempr"]
        
    # delete folders in model directory. removes all files.
    for i in directories:
        if os.path.exists(os.path.join(config_file.model_directory_path,i)):
          shutil.rmtree(os.path.join(config_file.model_directory_path,i))
          
    # create blank directories in model directory
    for i in directories:
        os.mkdir(os.path.join(config_file.model_directory_path,i))
    
    # remove forecast weather data r2c's
    # files from met/ & /tem dirs
    if tem:
      path = os.path.join(config_file.repository_directory, config_file.weather_data_directory,"tem","*.*")
      files = glob.glob(path)
      for i in files:
          os.remove(i)
          
    if met:
      path = os.path.join(config_file.repository_directory, config_file.weather_data_directory,"met","*.*")
      files = glob.glob(path)
      for i in files:
          os.remove(i)
    
    # remove r generate analysis png's
    path = os.path.join(config_file.repository_directory, config_file.r_graphics_directory,"*.*")
    files = glob.glob(path)
    for i in files:
        os.remove(i)
        
    # remove forecast files
    path = os.path.join(config_file.repository_directory,config_file.forecast_directory,"*.*")
    files = glob.glob(path)
    for i in files:
        os.remove(i)
        
    

def generate_spinup_event_files(config_file, start_date, end_date):
    """
    Event files specific to spin up. end date is provided as full date to end of last year to lwcb db. must be endYear0101.
    
    Args:
        config_file: see class ConfigParse
        start_date: string in the format "YYYY/MM/DD", typically "YYYY/01/01"
        end_date: string in the format "YYYY/MM/DD", typically "YYYY/01/01"
    Returns:
        NULL - but generates .evt files (ASCII)
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
      pre_process.EventGenerator(config_file, 
                         start_date = event_start, 
                         first_event = True, 
                         events_to_follow = False,
                         flags = [[":resumflg", "n"],[":tbcflg", "y"]])
      return #get out of function if single year

    #get range of years
    Spinup_Years = range(start_year,end_year+1)
    

    #loop through each year
    for i,event_year in enumerate(Spinup_Years):
      event_start = str(event_year) + "/01/01"
      
      #first event file
      if i == 0:
        stringtoappend = "0101.evt"
        yearstofollow = [str(s) + stringtoappend for s in range(event_year+1,end_year+1)]
        pre_process.EventGenerator(config_file, 
                                   start_date = event_start, 
                                   first_event = True, 
                                   events_to_follow = yearstofollow,
                                   flags = [[":resumflg", "n"],[":tbcflg", "n"]])
        
      if i!= 0:
        #middle event files
        if event_year != (end_year):
            pre_process.EventGenerator(config_file, 
                                       start_date = event_start, 
                                       first_event = False, 
                                       events_to_follow = False,
                                       flags = [[":resumflg", "n"],[":tbcflg", "n"]])
                                   
        #last event file
        if event_year == (end_year):
            pre_process.EventGenerator(config_file, 
                                       start_date = event_start, 
                                       first_event = False, 
                                       events_to_follow = False,
                                       flags = [[":resumflg", "n"],[":tbcflg", "y"]])
          
      
     

    
       
def generate_spinup_generic_files(config_file, start_date):
    """
    Generates generic data files only for spin up.  generated from templates in the 'lib' directory
    
    Args:
        config_file: see class ConfigParse
        start_date: string in the format "YYYY/MM/DD", typically "YYYY/01/01"

    """
    
    print "Generating snow and moist files"
    
    # generate swe.r2c, write to snow1 directory
    pre_process.GenericTemplateWriter(config_file, template_name = "TEMPLATE_swe.r2c", start_date = start_date)
       
    # generate psm.pt2, write to moist directory
    pre_process.GenericTemplateWriter(config_file, template_name = "TEMPLATE_gsm.r2c", start_date = start_date)
    
    


def query_lwcb_db(config_file, start_date, end_date):
    """
    Query lwcb db & convert to required tb0 format. This is sub'd out to an R-script.

    Args:
        config_file: see class ConfigParse
        start_date: string in the format "YYYY/MM/DD"
        end_date: string in the format "YYYY/MM/DD"
    Returns:
        NULL - but generates WATFLOOD .tb0 files
    """
    
    print "Getting historical data from DB..."
    
    # res releases
    if config_file.use_resrel == "True":
      cmd = [config_file.rscript_path,
            os.path.join(config_file.r_script_directory, config_file.r_script_lwcb_query),
            config_file.r_script_directory, #1
            config_file.model_directory_path,#2
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
          config_file.model_directory_path,
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
          config_file.model_directory_path,
          "level","level",
          start_date,
          end_date,
          config_file.lwcb_db_path,
          config_file.lwcb_station_level,
          config_file.nudge_strmflws]
    subprocess.call(cmd,shell=True)
    
    # database precipitation if no CaPA
    if config_file.use_capa == "False":  
        # precipitation
        cmd = [config_file.rscript_path,
              os.path.join(config_file.r_script_directory, config_file.r_script_lwcb_query),
              config_file.r_script_directory,
              config_file.model_directory_path,
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
          config_file.model_directory_path,
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
          config_file.model_directory_path,
          "strfw","strfw",
          start_date,
          end_date,
          config_file.lwcb_db_path,
          config_file.lwcb_station_streamflow,
          config_file.nudge_strmflws]
    subprocess.call(cmd,shell=True)
      
    # database temperature (point) if not using GEM data
    if config_file.use_GEMTemps == "False":
      cmd = [config_file.rscript_path,
            os.path.join(config_file.r_script_directory, config_file.r_script_lwcb_query),
            config_file.r_script_directory,
            config_file.model_directory_path,
            "tempg","tempg",
            start_date,
            end_date,
            config_file.lwcb_db_path,
            config_file.lwcb_station_temperature,
            config_file.nudge_strmflws]
      subprocess.call(cmd,shell=True)
    
    

def setup_members(config_file,member):
    """
    Function to clean up the working 'Repo' directory of the specfied member and
    copy and modify the reservoir release files

    Args:
        config_file: see class ConfigParse
        member: name of hydrological ensemble member
    
    Returns:
        NULL
    """
    
    #clean up the member repository
    member_repository = os.path.join(os.path.dirname(os.path.dirname(config_file.repository_directory)), member, "Repo")
    clean_up(member_repository)
        
    #copy the reservoir release files from the 'mothership' and modify the coefficients as required
    CopyModResrl(os.path.join(config_file.repository_directory, model_directory, "resrl"),
                 os.path.join(member_repository, config_file.model_directory, "resrl"),
                 os.path.join(member_repository, config_file.lib_directory, "template_rel.tb0"))

                 
                 
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
    
    CopyModEvent(os.path.join(config_file.model_directory_path,"event"),
                 os.path.join(member_repository,model_directory,"event"),
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
            input[2]: use_forecast - toggle for plotting on whether to append forecast, set to False for the spinup
            
    Returns:
        NULL
    """
    
    #parse input
    config_file = input[0]
    member_directory = input[1]
    use_forecast = input[2]
    
    #execute spinup
    execute_watflood(config_file, member_directory)
    
    #plot results
    post_process.generate_hydrographs(config_file, member_directory,use_forecast) 
  
    #copy results
    print member_directory
    if os.path.exists(os.path.join(os.path.dirname(member_directory), "Repo_spinup")):
        shutil.rmtree(os.path.join(os.path.dirname(member_directory), "Repo_spinup"), onerror = onerror)
    shutil.copytree(os.path.join(os.path.dirname(member_directory), "Repo"),
                                os.path.join(os.path.dirname(member_directory), "Repo_spinup"),
                                ignore = shutil.ignore_patterns(config_file.weather_data_directory, config_file.bin_directory))
                                
                                
                                
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
            input[2]: use_forecast - toggle for plotting on whether to append forecast, set to False for the hindcast
            
    Returns:
        NULL
    """
    
    #parse inpute
    config_file = input[0]
    member_directory = input[1]
    use_forecast = input[2]
    
    #execute hindcast
    execute_watflood(config_file, member_directory)

    #plot results
    post_process.generate_hydrographs(config_file,member_directory,use_forecast) 
  
    #copy results
    print member_directory
    if os.path.exists(os.path.join(os.path.dirname(member_directory), "Repo_hindcast")):
        shutil.rmtree(os.path.join(os.path.dirname(member_directory), "Repo_hindcast"), onerror = onerror)
    shutil.copytree(os.path.join(os.path.dirname(member_directory), "Repo"),
                                os.path.join(os.path.dirname(member_directory), "Repo_hindcast"),
                                ignore = shutil.ignore_patterns(config_file.weather_data_directory, config_file.bin_directory))
                                
                                
                                
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
            input[2]: RunName - specifies which meteorological ensemble member used
            
    Returns:
        NULL
    """
    
    #parse input file
    config_file = input[0]
    member_directory = input[1]
    RunName = input[2]
    
    #run watflood
    execute_watflood(config_file,member_directory)
  
    #save results to common folder
    shutil.copyfile(os.path.join(member_directory, config_file.model_directory, "results", "spl.csv"),
                    os.path.join(member_directory, config_file.forecast_directory, "spl" + RunName + ".csv"))
                    
    shutil.copyfile(os.path.join(member_directory, config_file.model_directory, "results", "resin.csv"),
                    os.path.join(member_directory, config_file.forecast_directory, "resin" + RunName + ".csv"))
    
    
    
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
            input[2]: use_forecast - toggle for plotting on whether to append forecast, set to True for Forecast
            
    Returns:
        NULL
    """
    
    config_file = input[0]
    member_directory = input[1]
    use_forecast = input[2]
    
    #plot results
    post_process.generate_hydrographs(config_file,member_directory, use_forecast) 
  
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
        
        
def CopyModEvent(mothership_dir, member_dir, keywords = "NA"):
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
    used inside class ConfigParse
    
    Args:
        configuration_file: path to config file
        
    Returns:
        parameter_settings: dictionary of all the data in the config text file
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
                parameter_settings[key] = value
    
    return parameter_settings

    


def getDateTime(hours):
    """
    gets a DateTime hours hours from midnight this morning
    
    Args:
        hours: integer, see grib2r2c function
        
    Returns:
        newdate: today's date at time = 0
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
        
    Returns:
        NULL - but may build a directory 
    """

    d = os.path.dirname(directory)
    if not os.path.exists(d):
        os.makedirs(d)
  

def generate_hindcast_event_file(config_file, start_date, resume_toggle = False, tbc_toggle = False):
    """
    creates event file with :noeventstofollow set to 0. used to run distribution executables.
    
    Args:
        config_file: see class ConfigParse
        start_date: string in the format 'YYYY/MM/DD'
        resume_toggle: turns the resumeflg on or off in event file
        tbc_toggle: turns the tbcflg on or off in event file
        
    Returns:
        NULL - but generates .evt file
    """

    if resume_toggle is True:
        resflag = "y"
    else:
        resflag = "n"
        
    if tbc_toggle is True:
        tflag = "y"
    else:
        tflag = "n"

    pre_process.EventGenerator(config_file, 
                             start_date = start_date, 
                             first_event = True, 
                             events_to_follow = False,
                             flags = [[":resumflg", resflag,],[":tbcflg", tflag]])
                             

                             

def generate_run_event_files_forecast(config_file, members):
    """
    Creates the event files, executes WATFLOOD and saves output for each of the ensemble met forecasts.
    The met files in the radcl folder are referenced as the master list. If corresponding files are not found
    (ie. there are multiple met ensemble files but only a single temperature file) in the tempr directory, 
    the last working temperature files are used.
    
    If multiple hydrological ensembles are being used, these are executed in parallel.
    
    Args:
        config_file: see class ConfigParse
        members: list of hydrological ensemble members
     
    Returns:
        NULL - but produces event files, executes WATFLOOD and saves results files
    """
    print "Generating event files and executing WATFLOOD..."


    #get list of met and temp files
    met_list = sorted(os.listdir(config_file.model_directory_path + "/radcl"))
    tempr_list = os.listdir(config_file.model_directory_path + "/tempr")
    tem_list = sorted([s for s in tempr_list if "tem" in s])
    dif_list = sorted([s for s in tempr_list if "dif" in s])
    
    #Use the met files as the 'master copy', get the simulation # from each filename
    RunNumber = [re.findall(r'met_(\d+)-(\d+).+', s) for s in met_list]
    
    #for each simulation in the 'master'
    for i,Run in enumerate(RunNumber):
      #Parse simulation Run number
      RunName = Run[0][0] + '-' + Run[0][1]
      print "Running Scenario: " + RunName

      #assign the temperature file name, if it doesn't exist, use the most recent working temperature file
      try:
        tem_list[i]
      except IndexError:
        print "using default temp file \n"
      else:
        new_temperature_file = tem_list[i]
        new_tempdiff_file = dif_list[i]
        
      #generate the event file, changing the met and tem references accordingly
      pre_process.EventGenerator(config_file, 
                         start_date = config_file.forecast_date, 
                         first_event = True, 
                         events_to_follow = False,
                         flags = [[":resumflg", "y"],
                                  [":tbcflg", "n"],
                                  [":griddedrainfile","radcl\\" + met_list[i]],
                                  [":griddedtemperaturefile","tempr\\" + new_temperature_file],
                                  [":griddeddailydifference","tempr\\" + new_tempdiff_file]])
    
      #copy to other members
      for i in members:
        copy_memberevents(config_file,i)

      #execute parallel program to loop through each met forecast and run watflood
      #set input for Mothership and inputs, this can be done in a loop because it is fast
      input = [[config_file,config_file.repository_directory,RunName]] #MotherShip input
      for j,member in enumerate(members): #member input
          member_repository = os.path.join(os.path.dirname(os.path.dirname(config_file.repository_directory)), member,"Repo")
          input.append([config_file,member_repository,RunName])
          
      #execute and save each member in parallel
      pool = multiprocessing.Pool(processes = len(members) + 1)
      pool.map(execute_and_save_forecast,input)
        
        

def generate_forecast_streamflow_file(config_file):
    """
    Generates Streamflow file for the forecast. Streams need to have a '-1' for each day that the forecast runs
    because WATFLOOD bases it's duration off this file
    
    Args:
        config_file: see class ConfigParse
        
    Returns:
        NULL - but generates *_str.tb0 file
    """
    
    # forecast start date used
    pre_process.StreamFlowGenerator(config_file, "TEMPLATE_str.tb0", start_date = config_file.forecast_date, NumDays = 10)


def generate_forecast_releases_file(config_file):
    """
    Generates reservoir release file for forecast. This sets the reservoir releases to -1 for any reservoir that has a volume-discharge curve,
    and to today's estimated release for any reservoir where outflow is forced. This discharge is assumed for the duration of the forecast.
    An R-script is used to do this as it queries the LWCB database.
    
    Args:
        config_file: see class ConfigParse
        
    Retunrs:
        NULL - but generates *_rel.tb0 file
    """
    
    #set Rscript command
    cmd = [config_file.rscript_path,os.path.join(config_file.r_script_directory,config_file.r_script_lwcb_query),
                                      config_file.r_script_directory,config_file.model_directory_path,"resrl","rel",
                                      config_file.forecast_date,config_file.forecast_date,
                                      config_file.lwcb_db_path,config_file.lwcb_station_resrel]
    subprocess.call(cmd,shell=True)


def generate_forecast_inflows_file(config_file):
    """
    Generates Reservoir Inflow file for the forecast. Inflows are '-1' for each day that the forecast runs. This ensures that a resin.csv file
    is created for these reservoirs.
    
    Args:
        config_file: see class ConfigParse
        
    Returns:
        NULL - but generates *_rin.tb0 file
    """
    # forecast start date used
    pre_process.ResInflowGenerator(config_file, "TEMPLATE_rin.tb0", start_date = config_file.forecast_date, NumDays = 10)



def generate_forecast_diversions_file(config_file):
    """
    Generates diversion release file for forecast. This sets the Root River diversion to today's estimated release. 
    This released is assumed for the duration of the forecast. An R-script is used to do this as it queries the LWCB database.
    
    Args:
        config_file: see class ConfigParse
        
    Retunrs:
        NULL - but generates *_div.tb0 file
    """
    
    # generate div_pt2, write to diver directory
    cmd = [config_file.rscript_path,os.path.join(config_file.r_script_directory,config_file.r_script_lwcb_query),config_file.r_script_directory,
          config_file.model_directory_path,"diver","diver",config_file.forecast_date,config_file.forecast_date,
          config_file.lwcb_db_path,config_file.lwcb_station_diver]
    subprocess.call(cmd,shell=True)




def generate_forecast_files(config_file):
    """
    Generates following 4 forecast files. streamflow, reserviour release, resevoir inflows & diversions.
    
    Args:
        config_file: see class ConfigParse
        
    Retunrs:
        NULL - but generates .tb0 files
    """
    
    print "Generating streamflow, reservoir and diversion forecast files..."
    generate_forecast_streamflow_file(config_file)
    generate_forecast_releases_file(config_file)
    generate_forecast_inflows_file(config_file)
    generate_forecast_diversions_file(config_file)
    
    print "\n"

       

    
def calculate_distributed_data(config_file, snow, moist):
    """
    Run distribution models. moist.exe, snw.exe run if the arguments are set, ragmet.exe, tmp.exe only if no capa/ no GEMtemps selected by
    user in configuration file. Executables must be run from the root of model directory.
    
    Args:
        config_file: see class ConfigParse
        
    Retunrs:
        NULL - but runs distribution executables
    """
    print "Calculating Distributed Data"
    
    # initial directory
    initial_directory = os.getcwd()
    
    # change directory to root of model directory
    os.chdir(os.path.join(config_file.repository_directory, config_file.model_directory_path))
    
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
    if snow == True:
      cmd = [os.path.join(config_file.repository_directory,
                          config_file.bin_directory,
                          config_file.data_distribution_snow)]   
      subprocess.call(cmd,shell=True)
	
    # moist exe
    if moist == True:
      cmd = [os.path.join(config_file.repository_directory,
                          config_file.bin_directory,
                          config_file.data_distribution_moist)]   
      subprocess.call(cmd,shell=True)
    
    # reset directory to initial
    os.chdir(initial_directory)

    

def update_model_folders(config_file):
    """
    Move met and tem files from the temporary wxData folder to the radcl and tempr directories within the WATFLOOD folder structure
    After the files have been moved, generate *_diff.r2c (required for modified Hargreaves evaporation (:flgevp2 = 4 in par file) 
    files from the *_tem.r2c files using a custom Rscript.
    
    Args:
        config_file: see class ConfigParse
        
    Returns:
        NULL - but moves files to proper directories and generates *_dif.r2c files
    """
    
    #define function from http://stackoverflow.com/questions/1868714/how-do-i-copy-an-entire-directory-of-files-into-an-existing-directory-using-pyth
    def copytree(src, dst, symlinks=False, ignore=None):
      for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, symlinks, ignore)
        else:
            shutil.copy2(s, d)
    
    #= move forecast generated r2c files into appropriate model folders. data is always generated. 
    # data currently created in wxData/met --> model_directory_path/radcl & wxData/tem --> model_directory_path/tempr
    # copy precipitation
    # get file name in directory
    forecast_met_directory = os.path.join(config_file.repository_directory, config_file.weather_data_directory, "met")
    current_file = os.listdir(forecast_met_directory)[0]
    copytree(forecast_met_directory, os.path.join(config_file.repository_directory, config_file.model_directory_path, "radcl"))
    
    # copy temperature
    forecast_tem_directory = os.path.join(config_file.repository_directory, config_file.weather_data_directory,"tem")
    current_file = os.listdir(forecast_tem_directory)[0]
    copytree(forecast_tem_directory,os.path.join(config_file.repository_directory,config_file.model_directory_path,"tempr"))
    
    #create YYYYMMDD_dif.r2c file from temperature file
    print "Calculating YYYYMMDD_dif.r2c file \n"
    cmd = [config_file.rscript_path, os.path.join(config_file.repository_directory, config_file.scripts_directory, config_file.r_script_tempdiff),
                                    os.path.join(config_file.repository_directory, config_file.scripts_directory)]

    subprocess.call(cmd,shell=True)

    

def execute_watflood(config_file, hydensemble_directory):
    """
    Execute watflood model, current directory must be model directory.
    
    Args:
        config_file: see class ConfigParse
        hydensemble_directory: the hydrological ensemble directory
        
    Returns:
        NULL - but executes WATFLOOD
    """

    # must change to root of model directory
    os.chdir(os.path.join(hydensemble_directory, config_file.model_directory))  
    
    cmd = [os.path.join(config_file.repository_directory,config_file.bin_directory,config_file.watflood_executable)]
    subprocess.call(cmd,shell=True)

    
    
def spinup_capa(config_file,spinup_start_date,spinup_end_date):
    """
    Copy CaPA r2c files from the CaPA repository into the WATFLOOD radcl folder
    
    Args:
        config_file: see class ConfigParse
        spinup_start_date: start date string in format "YYYY/MM/DD"
        spinup_end_date: end date string in format "YYYY/MM/DD"
        
    Returns:
        NULL - copies files
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
                  os.path.join(config_file.model_directory_path,"radcl"))
    
    
    
def spinup_GEMTemps(config_file, spinup_start_date, spinup_end_date):
    """
    Copy GEMTemps r2c files from the GEMTemps repository into the WATFLOOD radcl folder
    
    Args:
        config_file: see class ConfigParse
        spinup_start_date: start date string in format "YYYY/MM/DD"
        spinup_end_date: end date string in format "YYYY/MM/DD"
        
    Returns:
        NULL - copies files
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
                  os.path.join(config_file.model_directory_path,"tempr"))
      shutil.copy(os.path.join(config_file.historical_GEMTemps_path, start_date_dif),
                  os.path.join(config_file.model_directory_path,"tempr"))
    
    



def copy_resume(config_file, source_dir, member_path = "NA"):
    """
    Copy the resume files (flow_init.r2c, soil_init.r2c, resume.txt, lake_level_init.pt2) from a previously run
    simulation into the working directory (ie. the Repo/WATFLOOD directory)
    
    Args:
        config_file: see class ConfigParse
        source_dir: the previously run simulation - 'Repo_spinup' or 'Repo_hindcast'
        member_path: path to hydrological ensemble directory if applicable
     
    Returns:
        NULL - copies required files
    """

    #get full path of source directories
    print "Copying resume files from " + source_dir + "...." + "\n"
    
    #if no hydrologlical ensemble then use the standard 'mothership'
    if member_path == "NA":
      member_path = os.path.dirname(config_file.repository_directory)
    
    #delete \wpegr\flowinit.r2c,soilinit.r2c,resume.txt if exists
    resume_files = ["flow_init.r2c","soil_init.r2c","resume.txt","lake_level_init.pt2"]
    del_items = []
    make_items = []
    
    for i in resume_files:
      del_path = os.path.join(member_path, "Repo", config_file.model_directory,i)
      del_items.append(del_path)
      
      make_path = os.path.join(member_path, source_dir, config_file.model_directory, i)
      make_items.append(make_path)
        
    # delete \wpegr\level\20140101_ill.pt2 in dest directory if exists
    tmp = config_file.historical_start_date.split("/")
    ill_file = "%s%s%s" %(tmp[0],tmp[1],tmp[2]) + "_ill.pt2"
    ill_path = os.path.join(source_dir, config_file.model_directory, "level", ill_file)
    del_items.append(ill_path)
    
    for d in del_items: 
      if os.path.exists(d):
        os.remove(d)
        
    #copy \wpegr\flowinit.r2c,soilinit.r2c,resume.txt to dest directory from source directory
    for m in range(len(make_items)):
      shutil.copyfile(make_items[m],del_items[m])

    print "\n"
    
    

def UpdateConfig(config_file):
    """
    Script to make automatic changes to 'configuration.txt'
    Namely, changes the historical_end_date and the forecast_date to yesterday and today, respectively
    
    Args:
        config_file: see class ConfigParse
     
    Returns:
        NULL - updates config file with current dates
    """

    #first define a search and replace function
    def replace(file_path, pattern, subst):
        #Create temp file
        fh, abs_path = tempfile.mkstemp()
        new_file = open(abs_path,'w')
        old_file = open(file_path)
        for line in old_file:
            #new_file.write(line.replace(pattern, subst))
            new_file.write(re.sub(pattern, subst, line)) #http://stackoverflow.com/questions/16720541/python-string-replace-regular-expression?lq=1
        #close temp file
        new_file.close()
        os.close(fh)
        old_file.close()
        #Remove original file
        os.remove(file_path)
        #Move new file
        shutil.move(abs_path, file_path)
        
    #Get today's and yesterday's dates
    today_date = datetime.datetime.today()
    yesterday_date = today_date - datetime.timedelta(1)
        
    #replace dates in text file
    replace(config_file.configuration_file,r'historical_end_date:.+','historical_end_date:' + yesterday_date.strftime('%Y/%m/%d'))
    replace(config_file.configuration_file,r'forecast_date:.+','forecast_date:' + today_date.strftime('%Y/%m/%d'))    
    

class ConfigParse:
    """
    object to define all parameters in the configuration.txt file
    """
    
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
        self.lib_directory = parameter_settings["lib_directory"]
        self.forecast_directory = parameter_settings["forecast_directory"]
        self.scripts_directory = parameter_settings["scripts_directory"]
        # watflood folder "wpegr"
        self.model_directory = parameter_settings["model_directory"]
        self.model_directory_path = os.path.join(self.repository_directory,self.model_directory)
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
        self.r_graphics_directory = os.path.join(self.repository_directory,"diagnostic")

        # r script names for spl/resin analysis
        self.r_script_diagnostics_spl = parameter_settings["r_script_diagnostics_spl"]
        self.r_script_diagnostics_resin = parameter_settings["r_script_diagnostics_resin"]
        self.r_script_diagnostics_maps = parameter_settings["r_script_diagnostics_maps"]

        # script names
        self.r_script_lwcb_query = parameter_settings["r_script_lwcb_query"]
        self.r_script_lwcb_PT2query = parameter_settings["r_script_lwcb_PT2query"]
        self.r_script_r2cadjust = parameter_settings["r_script_r2cadjust"]
        self.r_script_lakelevels = parameter_settings["r_script_lakelevels"]
        self.r_script_tempdiff = parameter_settings["r_script_tempdiff"]
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




        # location of adjustment scripts
        self.precip_adjust = parameter_settings["precip_adjust"]
        self.temp_adjust = parameter_settings["temp_adjust"]
        
        

    

