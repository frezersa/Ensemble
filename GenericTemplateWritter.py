#############################################################################################
# generic tb0 template writter. takes template file, date in YYYY/MM/DD, directory to write file to & file suffix (_ill.pt2)
#############################################################################################

import os
import argparse
import datetime

class args(object):
  pass

#define some helper functions

#returns a Date object from a string input (used to parse the command line argument)
def buildDate (input):
    return datetime.datetime.strptime(input, "%Y/%m/%d").date()
 
#returns a Time object from a string input (used to parse the command line argument) 
def buildTime (input):
  return datetime.datetime.strptime(input + ":00:00", "%H:%M:%S").time()
  
#Get command line arguments
data = args()
parser = argparse.ArgumentParser()
parser.add_argument('template_name', help="template name with extension. path will be defined relative to /../lib")
parser.add_argument('write_directory', help="full path of model directory with final folder")
parser.add_argument('file_suffix', help="file suffix with extenion (omit the underscore. it will be added). i.e ill.pt2")
parser.add_argument('date', type=buildDate , nargs=1, help="format: yyyy/mm/dd")
parser.add_argument('--hour', type=buildTime , default='00', help="format: HH; Auto fills to HH:00:00")
parser.parse_args(namespace=data)


#initialize useful variables
Path = os.path.split(os.path.abspath(__file__))[0]
file = open(Path + '/../lib/' + data.template_name, 'rb') #This is the template file used to build from
table = [row.strip().split() for row in file]

i = 0

#build new table from Template
#NOTE: ColumnName MUST come before the coefficients in the TEMPLATE file    
indices = []
for i, line in enumerate(table):
    #fix some of the meta data
    if line[0] == ':CreationDate':
        table[i][1] = datetime.datetime.now().strftime("%Y-%m-%d")
        table[i][2] = datetime.datetime.now().strftime("%H:%M")
    
    if line[0] == ':StartDate':
        table[i][1] = data.date[0].strftime("%Y/%m/%d")
    
    if line[0] == ':StartTime':
        table[i][1] = data.hour.strftime("%H:%M:%S")

    #get column indices of stations  
    #if line[0] == ':ColumnName':
    #    for j, val in enumerate(line):
    #        if val in stations:
    #            indices.append(j)


# write tb0 file
file = open(os.path.join(data.write_directory,data.date[0].strftime("%Y%m%d") + "_" + data.file_suffix), 'w')

#output the new data    
for i, line in enumerate(table):   
    for j, val in enumerate(line):
        if j is 0:
            file.write(str(val.ljust(20))),
        else:
            file.write(str(val.rjust(15))),
    file.write("\n")

file.close()
