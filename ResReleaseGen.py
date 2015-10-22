#############################################################################################
#Takes a date and Template file to build a new one with the coeffecients on the stations defined 
#by :ZeroRelease in the config file set to zero. Also update the date information to the date
#given in the command line.
#Output is given to standard output so it will likely have to be piped to a file to be useful
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
parser.add_argument('date', type=buildDate , nargs=1, help="format: yyyy/mm/dd")
parser.add_argument('-forecast', action='store_true', help="only applicable for forecast, writes zeros for selected stations")
parser.add_argument('--hour', type=buildTime , default='00', help="format: HH; Auto fills to HH:00:00")
parser.parse_args(namespace=data)

#initialize useful variables
Path = os.path.split(os.path.abspath(__file__))[0]
file = open(Path + '/../lib/TEMPLATE_rel.tb0', 'rb') #This is the template file used to build from
table = [row.strip().split() for row in file]

i = 0

#get station names from config file
openfile = Path + '/../../configuration.txt'
stations = []
for line in open(openfile):
    tokens = line.strip().split()
    # deal with white space. indexerror if list is 0 when attempting to pop
    if len(tokens) == 0:
        continue
    if tokens.pop(0) == ':ZeroRelease':
        while (tokens):
            stations.append(tokens.pop(0))

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
    if line[0] == ':ColumnName':
        for j, val in enumerate(line):
            if val in stations:
                indices.append(j)
	
	#write 0's for selected stations
	#set coefficients to zero for designated stations     
    if line[0].find('coeff') != -1 and data.forecast == True:
        for j, val in enumerate(line):
            if j in indices:
                table[i][j] = '0.0000E+00'

# write tb0 file
file = open(Path + '/../wpegr/resrl/' +  data.date[0].strftime("%Y%m%d") + '_rel.tb0', 'w')

#output the new data    
for i, line in enumerate(table):   
    for j, val in enumerate(line):
        if j is 0:
            file.write(str(val.ljust(20))),
        else:
            file.write(str(val.rjust(15))),
    file.write("\n")

file.close()
    