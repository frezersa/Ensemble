"""
# Richard Burcher
# NRC
# 2013

LWCB Framework script to generate all neccessary files to allow WATFLOOD model to execute. 

This is 1 of 2 scripts; the other script LWCB_Framework_Accept_Model_Results.py is used to 
create a final model folder containg various output files, graphics and a HEC-DSS db containing
the forecasted simulated resin.csv data.


Allows user to perform a 2 year spinup period prior to model run. User can perform a default
forecast or choose to apply a state variable update (only permitted from jan0101) to 3 different areas (precipitation scale factor,
use observed streamflow or provide a new snowcourse file.)

Pulls data from LWCB db, downloads CAPA and Forecasted data from EC online repository.

All settings read from a configuration file that is user editable.

For each model execution, a series of R script generated graphics are produced & written to 
../diagnostic. User can decide if state variable adjustment is required. If not, user runs
LWCB_Framework_Accept_Model_Results.py

"""


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
from FrameworkLibrary import *

class args(object):
  pass

data = args()
parser = argparse.ArgumentParser()
parser.add_argument('-c','--Config',help='Full path to the configuration file.')
parser.add_argument('-m','--ModelRun',help='Type of model run: Spinup,DefaultHindcast,HindcastAdjust,Forecast')
parser.parse_args(namespace=data)

## read configuration file
config_file = ConfigParse(data.Config) #config_file is a class that stores all parameters
model_run = data.ModelRun

#= set inital working directory to repository root folder
os.chdir(config_file.repository_directory)

    
    
## ===== run operational framework

#= spin up 
if model_run == "Spinup":
    print "\n===============creating spin up===================\n"
    
    #Prepare Directories
    clean_up(config_file.model_directory,
           config_file.weather_data_directory,
           config_file.r_graphics_directory)
    generate_spinup_event_files(config_file,
                                config_file.spinup_start_date, 
                                config_file.spinup_end_date)
    generate_spinup_generic_files(config_file,
                                  config_file.spinup_start_date,
                                  config_file.spinup_end_date)
    query_lwcb_db(config_file,
                  config_file.spinup_start_date,
                  config_file.spinup_end_date)
    if config_file.use_capa == "True":
        spinup_capa(config_file,
                    config_file.spinup_start_date,
                    config_file.spinup_end_date)
    if config_file.use_GEMTemps == "True":
        spinup_GEMTemps(config_file,
                        config_file.spinup_start_date,
                        config_file.spinup_end_date)
    calculate_distributed_data(config_file,
                               snow="False",
                               moist="False")
    
    CopyModEvent("C:\W\A_MS\Model_Repository\wpegr\event",
                  "C:\W\B\Model_Repository\wpegr\event",
                  "NA")
                  
    CopyModResrl("C:\\W\\A_MS\\Model_Repository\\wpegr\\resrl",
                  "C:\\W\\B\Model_Repository\\wpegr\\resrl",
                  "C:\\W\\B\\Model_Repository\\lib\\template_rel.tb0")
    
    
    # # execute watflood
    execute_watflood(config_file,config_file.model_directory)
    execute_watflood(config_file,"C:\W\B\Model_Repository\wpegr")
    
    # #plot results
    # generate_analysis_graphs(config_file,
                            # start_date = config_file.spinup_start_date)
  
    # #copy results
    # if os.path.exists(os.path.join(os.path.dirname(config_file.repository_directory), "Model_Repository_spinup")):
        # shutil.rmtree(os.path.join(os.path.dirname(config_file.repository_directory), "Model_Repository_spinup"), onerror=onerror)
    # shutil.copytree(os.path.join(os.path.dirname(config_file.repository_directory), "Model_Repository"),
                                # os.path.join(os.path.dirname(config_file.repository_directory), "Model_Repository_spinup"),
                                # ignore = shutil.ignore_patterns("wxData", "bin"))
      


# using previous spin up for default forecast
elif model_run == "DefaultHindcast":
    print "\nusing previously run spin up & running default hindcast\n"
    
    #Prepare Directories
    clean_up(config_file.model_directory,
           config_file.weather_data_directory,
           config_file.r_graphics_directory)
    copy_resume(config_file, "Model_Repository_spinup")
    query_lwcb_db(config_file,
                  start_date = config_file.historical_start_date,
                  end_date = config_file.historical_end_date)
    query_ec_datamart_hindcast(config_file)
    generate_distribution_event_file(config_file,
                                     resume_toggle = "True", 
                                     tbc_toggle = "True")
    calculate_distributed_data(config_file,
                               snow = "False",
                               moist = "False",)

    # execute watflood
    execute_watflood(config_file)
    
    #plot results
    generate_analysis_graphs(config_file,
                            start_date = config_file.historical_start_date)

    #copy results
    if os.path.exists(os.path.join(os.path.dirname(config_file.repository_directory), "Model_Repository_hindcast")):
      shutil.rmtree(os.path.join(os.path.dirname(config_file.repository_directory), "Model_Repository_hindcast"), onerror=onerror)
    shutil.copytree(os.path.join(os.path.dirname(config_file.repository_directory), "Model_Repository"),
                                os.path.join(os.path.dirname(config_file.repository_directory), "Model_Repository_hindcast"),
                                ignore = shutil.ignore_patterns("wxData", "bin"))
                                
                                
                                

elif model_run == "Forecast":
    # print "Running Forecast\n"
    
    #Prepare Directories
    clean_up(config_file.model_directory,
            config_file.weather_data_directory,
            config_file.r_graphics_directory)
    copy_resume(config_file,"Model_Repository_hindcast")
    generate_forecast_files(config_file)
    query_ec_datamart_forecast(config_file)
    update_model_folders(config_file)
    
    # execute watflood (loop for meteorological ensemble)
    generate_model_event_files_forecast(config_file)
    
    #plot results
    generate_analysis_graphs(config_file,
                             start_date = config_file.historical_start_date,
                             resin = os.path.join(os.path.dirname(config_file.repository_directory), "Model_Repository/forecast/resin1-00.csv"),
                             spl =  os.path.join(os.path.dirname(config_file.repository_directory), "Model_Repository/forecast/spl1-00.csv"),
                             spinup = os.path.join(os.path.dirname(config_file.repository_directory), "Model_Repository_hindcast"))
    generate_meteorlogical_graphs(config_file)
    generate_ensemble_graphs(config_file)
    # generate_dss(hecdss_vue_path,r_script_directory,hec_writer_script)

    #copy results
    if os.path.exists(os.path.join(os.path.dirname(config_file.repository_directory), "Model_Repository_forecast")):
      shutil.rmtree(os.path.join(os.path.dirname(config_file.repository_directory), "Model_Repository_forecast"),onerror=onerror)
    shutil.copytree(os.path.join(os.path.dirname(config_file.repository_directory), "Model_Repository"),
                                os.path.join(os.path.dirname(config_file.repository_directory), "Model_Repository_forecast"),
                                ignore = shutil.ignore_patterns("wxData", "bin"))
                                
                                
                                

# elif model_run == "HindcastAdjust":
    # print "adjusting hindcast"
    # precip_toggle = "True"
    # temp_toggle = "True"
    
    # # while precip_toggle == "True" or temp_toggle == "True":
    # copy_resume(config_file,"Model_Repository_spinup")
    # adjust_hindcast(precip_toggle,temp_toggle)
    
        
    # # copy everything to new hindcast folder
    # if os.path.exists(os.path.join(os.path.dirname(repository_directory),"Model_Repository_hindcast_adjusted")):
      # shutil.rmtree(os.path.join(os.path.dirname(repository_directory),"Model_Repository_hindcast_adjusted"))
    # shutil.copytree(os.path.join(os.path.dirname(repository_directory),"Model_Repository"),os.path.join(os.path.dirname(repository_directory),"Model_Repository_hindcast_adjusted"),ignore=ignore_wxData)
      
    
      
# elif model_run == "RerunForecast":
    # print "Re-Running Forecast\n"
    # generate_model_event_files_forecast(historical_start_date,forecast_date)
    
    # #generate plots
    # generate_analysis_graphs(forecast_date,historical_start_date,model_directory,os.path.join(os.path.dirname(repository_directory),"Model_Repository/forecast/resin1-00.csv"),os.path.join(os.path.dirname(repository_directory),"Model_Repository/forecast/spl1-00.csv"),r_script_directory,r_graphics_directory,r_script_analysis_resin,r_script_analysis_spl,"2014-04-01","NA", os.path.join(os.path.dirname(repository_directory),"Model_Repository_hindcast_adjusted"))
    # generate_meteorlogical_graphs(r_script_directory,r_script_forecast,r_graphics_directory)
    # generate_ensemble_graphs(r_script_directory,r_script_ensemblegraphs,r_graphics_directory)
    # # generate_dss(hecdss_vue_path,r_script_directory,hec_writer_script)

    # # copy everything to new hindcast folder
    # if os.path.exists(os.path.join(os.path.dirname(repository_directory),"Model_Repository_forecast")):
      # print os.path.join(os.path.dirname(repository_directory),"Model_Repository_forecast")
      # shutil.rmtree(os.path.join(os.path.dirname(repository_directory),"Model_Repository_forecast"))
    # shutil.copytree(os.path.join(os.path.dirname(repository_directory),"Model_Repository"),os.path.join(os.path.dirname(repository_directory),"Model_Repository_forecast"),ignore=ignore_wxData)
      

    

else:
    print "\noptions selected are not correct. please review configuration settings.\n"
