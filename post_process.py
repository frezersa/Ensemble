import os
import datetime
import sys
import subprocess
import re



    
    
    
def generate_hydrographs(config_file,member_directory,use_forecast):
    """
    generates R daily graphics based on output of model resin & spl png files. output to /diagnostic folder
    """
    
    print "generating probablistic data"
    cmd = [config_file.rscript_path,
          os.path.join(config_file.r_script_directory, config_file.r_script_diagnostics_resin),
          os.path.join(member_directory,"scripts"), config_file.model_directory, use_forecast]
    subprocess.call(cmd,shell=True)
    
    cmd = [config_file.rscript_path,
          os.path.join(config_file.r_script_directory, config_file.r_script_diagnostics_spl),
          os.path.join(member_directory,"scripts"), config_file.model_directory, use_forecast]
    subprocess.call(cmd,shell=True)
    

    

def generate_meteorlogical_graphs(config_file):
    """
    generates R daily graphics based on output of model resin & spl png files. output to /diagnostic folder
    """
    

    print "Generating meteorlogical plots..."
    #get the first met and tem files in forecast directory
    met_list = sorted(os.listdir(os.path.join(config_file.model_directory, "radcl")))
    tempr_list_all = sorted(os.listdir(os.path.join(config_file.model_directory, "tempr")))
    tempr_list = [s for s in tempr_list_all if "tem" in s]
    
    #get met files in hindcast directory
    source_dir = os.path.join(os.path.dirname(config_file.repository_directory), "Repo_hindcast")
    met_hind_list = sorted(os.listdir(os.path.join(source_dir, "wpegr", "radcl")))
    
    #get first file in each of the directorys
    met_str_forecast = os.path.join(config_file.model_directory, "radcl", met_list[0])
    tem_str_forecast = os.path.join(config_file.model_directory, "tempr", tempr_list[0])
    met_str_hindcast = os.path.join(source_dir, "wpegr", "radcl", met_hind_list[0]) #this assumes there is only one hindcast file
    
    #run the R-script to generate meteorological plots
    cmd = [config_file.rscript_path, os.path.join(config_file.r_script_directory, config_file.r_script_diagnostics_maps),
            config_file.r_script_directory,
            config_file.r_graphics_directory,
            met_str_forecast,
            tem_str_forecast,
            met_str_hindcast,
            config_file.forecast_date]
    subprocess.call(cmd,shell=True)
    
      
def generate_dss(hecdss_vue_path,r_script_directory,hec_writer_script):
    inputfile = os.path.join(r_script_directory,"../diagnostic/Prob_forecast.csv")
    outputfile = os.path.join(r_script_directory,"../diagnostic/HECfile.dss")
    
    if not os.path.isfile(inputfile):
      print "Error: the input file: '" + str(inputfile) + "' does not exist \n and hence a DSS file cannot be created. Please ensure file 'Prob_forecast.csv' exists in the diagnostic directory"

    cmd = [hecdss_vue_path,os.path.join(r_script_directory,hec_writer_script),outputfile,inputfile]
    #cmd = ["C:\Program Files (x86)\HEC\HEC-DSSVue\HEC-DSSVue.exe","C:\Test_Framework\EC_Operational_Framework\Model_Repository\scripts\Writer_hec_dss_prob.py","C:/Test_Framework/EC_Operational_Framework/Model_Repository/diagnostic/HECfile.dss","C:/Test_Framework/EC_Operational_Framework/Model_Repository/diagnostic/Prob_forecast.csv"]
    
    subprocess.call(cmd,shell=True)