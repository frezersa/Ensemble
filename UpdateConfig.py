#Script to make automatic changes to 'configuration.txt'
#Namely, changes the historical_end_date and the forecast_date to yesterday and today, respectively

#from http://stackoverflow.com/questions/39086/search-and-replace-a-line-in-a-file-in-python
from tempfile import mkstemp
from shutil import move
from os import remove, close
import re
from datetime import date, timedelta
import argparse

class args(object):
  pass

data = args()
parser = argparse.ArgumentParser()
parser.add_argument('-c','--Config',help='Full path to the configuration file.')
parser.parse_args(namespace=data)

## read configuration file
configuration = data.Config
#configuration = "C:\WR_WTFLD_Framework_D\configuration.txt"



def replace(file_path, pattern, subst):
    #Create temp file
    fh, abs_path = mkstemp()
    new_file = open(abs_path,'w')
    old_file = open(file_path)
    for line in old_file:
        #new_file.write(line.replace(pattern, subst))
        new_file.write(re.sub(pattern, subst, line)) #http://stackoverflow.com/questions/16720541/python-string-replace-regular-expression?lq=1
    #close temp file
    new_file.close()
    close(fh)
    old_file.close()
    #Remove original file
    remove(file_path)
    #Move new file
    move(abs_path, file_path)
    
#Get today's and yesterday's dates
today_date = date.today()
yesterday_date = date.today() - timedelta(1)
    
#replace dates in text file
replace(configuration,r'historical_end_date:.+','historical_end_date:' + yesterday_date.strftime('%Y/%m/%d'))
replace(configuration,r'forecast_date:.+','forecast_date:' + today_date.strftime('%Y/%m/%d'))

