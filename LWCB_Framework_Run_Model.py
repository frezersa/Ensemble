"""
James Bomhof
August 30, 2016


Runs the main operations for the WATFLOOD framework. Requires two arguments to be passed in when calling
the script.
-c 'full path to the configuration file'
-m 'Type of model run: Spinup,DefaultHindcast,HindcastAdjust,Forecast'

Functions are defined in the FrameworkLibrary.py file

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
import multiprocessing
# NRC pyEnSim. must be installed prior to use.
import pyEnSim.pyEnSim as pyEnSim

from FrameworkLibrary import *
import post_process


def main():
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
    members = filter(None,config_file.ensemble_members.split(",")) #find out which hydr. ensemble members to run

    #= set inital working directory to repository root folder
    os.chdir(config_file.repository_directory)

    
        
    ## ===== run operational framework

    #= spin up 
    if model_run == "UpdateConfig":
        print "\n===============Updating Configuration File with Today's dates===================\n"
        UpdateConfig(config_file)
        
        
        
    elif model_run == "Spinup":
        print "\n===============creating spin up===================\n"
        
        # Prepare Directories
        clean_up(config_file.repository_directory)
        generate_spinup_event_files(config_file,
                                    config_file.spinup_start_date, 
                                    config_file.spinup_end_date)
        generate_spinup_generic_files(config_file,
                                      config_file.spinup_start_date)
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
        
        for i in members:
          setup_members(config_file,i)
          copy_memberevents(config_file,i)

        # execute watflood
        input = [[config_file,config_file.repository_directory,"False"]] #MotherShip input
        for j,member in enumerate(members): #member input
          member_repository = os.path.join(os.path.dirname(os.path.dirname(config_file.repository_directory)), member,"Repo")
          input.append([config_file,member_repository,"False"])
          
        pool = multiprocessing.Pool(processes = len(members) + 1)
        #pool = multiprocessing.Pool(processes = 1)
        pool.map(execute_and_plot_spinup,input)



    # using previous spin up for default forecast
    elif model_run == "DefaultHindcast":
        print "\nusing previously run spin up & running default hindcast\n"
        
        # #Prepare Directories
        # clean_up(config_file.repository_directory)
        # copy_resume(config_file, "Repo_spinup")
        # query_lwcb_db(config_file,
                      # start_date = config_file.historical_start_date,
                      # end_date = config_file.historical_end_date)
        met_process.query_ec_datamart_hindcast(config_file)
        
        # #generate the event file, this may need to be executed again after the distribute data programs are run,
        # #not required in current setup
        # generate_hindcast_event_file(config_file,
                                     # start_date = config_file.historical_start_date,
                                     # resume_toggle = True, 
                                     # tbc_toggle = True)
                                     
        # calculate_distributed_data(config_file,
                                   # snow = False,
                                   # moist = False)

                                   
        # for i in members:
          # setup_members(config_file,i)
          # copy_memberevents(config_file,i)
          # member_path = os.path.join(os.path.dirname(os.path.dirname(config_file.repository_directory)), i)
          # copy_resume(config_file, "Repo_spinup", member_path=member_path)

        # # execute watflood and plot hydrographs
        # input = [[config_file,config_file.repository_directory,"False"]] #MotherShip input
        # for j,member in enumerate(members): #member input
          # member_repository = os.path.join(os.path.dirname(os.path.dirname(config_file.repository_directory)), member,"Repo")
          # input.append([config_file,member_repository,"False"])
          
        # pool = multiprocessing.Pool(processes = len(members) + 1)
        # pool.map(execute_and_plot_hindcast,input)

                                   
                                  

    elif model_run == "Forecast":
        print "Running Forecast\n"
        
        # Prepare Directories
        clean_up(config_file.repository_directory, met = True,tem = True)
        copy_resume(config_file,"Repo_hindcast")
        generate_forecast_files(config_file)
        met_process.query_ec_datamart_forecast(config_file)
        update_model_folders(config_file)
        
        for i in members:
          setup_members(config_file,i)
          member_path = os.path.join(os.path.dirname(os.path.dirname(config_file.repository_directory)), i)
          copy_resume(config_file, "Repo_hindcast", member_path=member_path)
          
          
        # execute watflood (this calls parallel processing for spl execution
        generate_run_event_files_forecast(config_file,members)

        post_process.generate_meteorlogical_graphs(config_file) #only for MotherShip
        
        #execute parallel program to generate diagnostics
        input = [[config_file,config_file.repository_directory]] #MotherShip input
        for j,member in enumerate(members): #member input
          member_repository = os.path.join(os.path.dirname(os.path.dirname(config_file.repository_directory)), member,"Repo")
          input.append([config_file,member_repository])
          
        pool = multiprocessing.Pool(processes = len(members) + 1)
        pool.map(analyze_and_plot_forecast,input)
        

        



    else:
        print "\noptions selected are not correct. please review configuration settings.\n"


if __name__ == "__main__":
    main()