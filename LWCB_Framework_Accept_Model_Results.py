"""
# Richard Burcher
# NRC
# 2013

Script ran after LWCB_Framework_Run_Model.py executed and user satisified with model results. 

Creates a timestamped forecast under model_repository/forecasted/ to hold following files:
 - resin & spl.csv's
 - generated R graphics
 - HEC-DSS db containing resin.csv simulated forecast values for stations
 - configuration file 

"""

import os
import shutil
import sys
import glob
import argparse
import subprocess
import time

class args(object):
  pass

data = args()
parser = argparse.ArgumentParser()
parser.add_argument('-c','--Config',help='Full path to the configuration file.')
parser.parse_args(namespace=data)

## read configuration file
configuration_file = data.Config

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


## read configuration text file
parameter_settings = parse_configuration_file(configuration_file)


# link parsed configuration file values here. one point to change!
repository_directory = parameter_settings["repository_directory"]
 #= directories mapping
forecast_directory = parameter_settings["forecast_directory"]
scripts_directory = parameter_settings["scripts_directory"]
output_directory = parameter_settings["output_directory"]
# watflood folder "wpegr"
model_directory = parameter_settings["model_directory"]
model_directory = os.path.join(repository_directory,model_directory)
 #= hec dss db
hec_writer_script = parameter_settings["hec_writer_script"]
 #= executables
hecdss_vue_path = parameter_settings["hecdss_vue_executable"]
# write r script resin/spl png's for analysis
r_graphics_directory = os.path.join(repository_directory,"diagnostic")
# forecast start date
forecast_date = parameter_settings["forecast_date"]

# configuration file extension. no dot.
configuration_extension = "txt"


#= set inital working directory to repository root folder
os.chdir(repository_directory)


def create_forecast_folder(output_directory):
    """
    create unique timestamped folder to hold each execution of operational framework.
    
    output name = forecast_YYYYMMDD_MMSS
    """
    
    # get local time object for timestamp
    tmp_time = time.localtime()
    # out name for directory
    dir_name = "forecast_%02d%02d%02d" %(tmp_time.tm_year,tmp_time.tm_mon,tmp_time.tm_mday)
    
    mkdir_path = os.path.join(output_directory,dir_name)
    
    # create directory
    if not os.path.exists(mkdir_path):
      os.mkdir(mkdir_path)
    
    # return path for output directory & local timestamp for naming
    return mkdir_path,tmp_time


def copytree(src, dst, symlinks=False, ignore=None):
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, symlinks, ignore)
        else:
            shutil.copy2(s, d)

# - create time stamped directory
write_directory,name_time = create_forecast_folder(output_directory)

# - copy files
#copy WATFLOOD forecast files
copytree(src=os.path.join(repository_directory,forecast_directory),dst=write_directory)
#Copy diagnostic plots, csvs and HECDSS
copytree(os.path.join(repository_directory,"diagnostic"),write_directory)
#Copy reservoir settings
copytree(os.path.join(repository_directory,"wpegr/resrl"),write_directory)
#copy parameter file
shutil.copyfile(os.path.join(repository_directory,"wpegr/basin/wpegr_par.csv"),os.path.join(write_directory,"wpegr_par.csv"))
#copy web index file
shutil.copyfile(os.path.join(repository_directory,"lib/index.php"),os.path.join(write_directory,"index.php"))
#copy configuration file
shutil.copyfile(configuration_file,os.path.join(write_directory,"configuration.txt"))


text_file = open(os.path.join(write_directory,"Comments.txt"),"w")
text_file.write("Forecast: %02d%02d%02d_%02d%02d" %(name_time.tm_year,name_time.tm_mon,name_time.tm_mday,name_time.tm_hour,name_time.tm_min))
text_file.write("/n Calibration D")
text_file.close()
# copy spl.csv from model_repository/model_directory/results
# shutil.copy(os.path.join(repository_directory,model_directory,"results","spl.csv"),write_directory)
# copy r generate graphics from model_repositroy/diagnostics
# files = glob.glob(os.path.join("diagnostic","*.png"))
# for file in files:
    # shutil.copy(file,write_directory)
# copy configuration file(s) from directory above model_repository
# files = glob.glob(os.path.join("../","*." + configuration_extension))
# for file in files:
    # shutil.copy(file,write_directory)

# - create new dss & write resin.csv data.
# load_data_dss(repository_directory,model_directory,scripts_directory,write_directory,forecast_date,name_directory,name_directory,hec_writer_script)
