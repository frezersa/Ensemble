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

ensemble_members = parameter_settings["ensemble_members"].split(',')

# configuration file extension. no dot.
configuration_extension = "txt"


#= set inital working directory to repository root folder
os.chdir(repository_directory)


def create_forecast_folder(output_directory,forecast_date):
    """
    create unique timestamped folder to hold each execution of operational framework.
    
    output name = forecast_YYYYMMDD_MMSS
    """
    
    # get local time object for timestamp
    tmp_time = time.strptime(forecast_date, "%Y/%m/%d")
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

write_directory,name_time = create_forecast_folder(output_directory,forecast_date)
ms_directory = os.path.dirname(repository_directory)
ms = os.path.basename(ms_directory)
main_directory = os.path.dirname(ms_directory)

ensemble_members.append(ms)

#remove any whitespaces
ensemble_members = filter(None, ensemble_members)



# # - copy files
#copy WATFLOOD forecast files
for i in ensemble_members:
  dst_path = os.path.join(write_directory,i)
  if not os.path.exists(dst_path):
    os.mkdir(dst_path)
  copytree(src=os.path.join(main_directory,i,"Repo_forecast",forecast_directory),dst=dst_path)
  shutil.copyfile(os.path.join(main_directory,i,"Repo_hindcast","wpegr","results","resin.csv"),os.path.join(dst_path,"resin_hindcast.csv"))
  shutil.copyfile(os.path.join(main_directory,i,"Repo_hindcast","wpegr","results","spl.csv"),os.path.join(dst_path,"spl_hindcast.csv"))

#plot and export key data
cmd = "Rscript C:\WR_Ensemble\A_MS\Repo\scripts\ProcessForecast.R C:\WR_Ensemble\A_MS\Repo\scripts " + write_directory
print cmd 
subprocess.call(cmd)

