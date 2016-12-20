"""
James Bomhof
August 30, 2016


Runs the main operations for the WATFLOOD framework. Requires two arguments to be passed in when calling
the script.
-c 'full path to the configuration file'
-m 'Type of model run: UpdateConfig,Spinup,DefaultHindcast,Forecast,AcceptAndCopy'

Functions are defined in the custom modules located in same folder (FrameworkLibrary.py,
met_process.py, post_process.py, pre_process.py, pyEnSim_basics.py)

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

# NRC pyEnSim. must be installed prior to use.
import pyEnSim.pyEnSim as pyEnSim

#import custom modules
import FrameworkLibrary
import post_process


def Run_Framework():
    #get arguments
    class args(object):
      pass

    data = args()
    parser = argparse.ArgumentParser()
    parser.add_argument('-c','--Config',help='Full path to the configuration file.')
    parser.add_argument('-m','--ModelRun',help='Type of model run: Spinup,DefaultHindcast,HindcastAdjust,Forecast')
    parser.parse_args(namespace=data)

    ## read configuration file
    config_file = FrameworkLibrary.ConfigParse(data.Config) #config_file is a class that stores all parameters
    model_run = data.ModelRun

    #= set inital working directory to repository root folder
    os.chdir(config_file.repository_directory)

    ## ===== run operational framework

    # if Update Configuration File (specifically the hindcast and forecast dates)
    if model_run == "UpdateConfig":
        print "\n===============Updating Configuration File with Today's dates===================\n"
        FrameworkLibrary.UpdateConfig(config_file)
        
    #= spin up 
    elif model_run == "Spinup":
        FrameworkLibrary.spin_up(config_file)
        
    # hindcast
    elif model_run == "DefaultHindcast":
        FrameworkLibrary.hindcast(config_file)
        
    # Forecast
    elif model_run == "Forecast":
        FrameworkLibrary.forecast(config_file)
        
    # Accept and Copy
    elif model_run == "AcceptAndCopy":
        FrameworkLibrary.AcceptAndCopy(config_file)

    else:
        print "\noptions selected are not correct. please review configuration settings.\n"


# see http://stackoverflow.com/questions/419163/what-does-if-name-main-do for description of next line
if __name__ == "__main__":
    Run_Framework()