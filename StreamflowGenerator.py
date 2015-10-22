import pprint
import os
import datetime
import argparse
import math

class args(object):
  pass

#define some helper functions

#returns a date object created from a string (used to parse a command line argument)
def buildDate (input):
    return datetime.datetime.strptime(input, "%Y/%m/%d").date()

#returns a time object created from a string (used to parse a command line argument) 
def buildTime (input):
    return datetime.datetime.strptime(input + ":00:00", "%H:%M:%S").time()
  
  
  
#Get arguments from command line
data = args()
parser = argparse.ArgumentParser()
parser.add_argument('startdate', type=buildDate , nargs=1, help="format: yyyy/mm/dd")
parser.add_argument('--starthour', type=buildTime , default='00', help="format: HH; Auto fills to HH:00:00")
parser.parse_args(namespace=data)

#initialize some useful variables
Path = os.path.split(os.path.abspath(__file__))[0]
file = open(Path + '/../lib/TEMPLATE_str.tb0', 'rb')
table = [row.strip().split() for row in file]

#get repo data from config file
getRepos = False
repos = []
for line in open(Path + '/../../configuration.txt'):
    tokens = line.strip().split()
	# deal with white space. indexerror if list is 0 when attempting to pop
    if len(tokens) == 0:
        continue
    if tokens[0] == ':SourceData':
        tokens.pop(0)
        getRepos = True
    elif tokens[0] == ':EndSourceData':  
        tokens.pop(0)
        getRepos = False
    elif getRepos:
        tokens.pop(0)
        repos.append(tokens)

#get number of days from beginning to end of forecast from acquired repo data
StartDTime = min(int(x) for x in repos[2])
EndDTime = max(int(x) for x in repos[3])
NumDays = int(math.ceil((float(EndDTime) - float(StartDTime))/24))

#seperate header data from table data 
i = 0
HeaderData = []
while (table[0][0] != ':endHeader') :
    HeaderData.append(table.pop(0))
HeaderData.append(table.pop(0))

#iterate through header data to change some things and get the number of stations
numStations = 0
for i, line in enumerate(HeaderData):

    #fix some of the meta data
    if line[0] == ':CreationDate':
        HeaderData[i][1] = datetime.datetime.now().strftime("%Y-%m-%d")
        HeaderData[i][2] = datetime.datetime.now().strftime("%H:%M")
        
    elif line[0] == ':StartDate':
        HeaderData[i][1] = data.startdate[0].strftime("%Y/%m/%d")
        
    elif line[0] == ':StartTime':
        HeaderData[i][1] = data.starthour.strftime("%H:%M:%S")
        
    #get the number of stations
    elif line[0] == ':ColumnName':
        numStations = len(line) - 1

		
# write tb0 file
file = open(Path + '/../wpegr/strfw/' +  data.startdate[0].strftime("%Y%m%d") + '_str.tb0', 'w')


#print the modified header data
for i, line in enumerate(HeaderData):
    for j, val in enumerate(line):
        if j is 0:
            file.write(str(val.ljust(20))),
        else:
            file.write(str(val.rjust(15)) + " "),
		
    file.write('\n')
    #print ""
	
#print a -1.000 for each station for each day 
for i in range (0,NumDays):
    print " ".ljust(20),
    for j in range(0,numStations):
        file.write(str("-1.000".rjust(15))),
    #print ""
    file.write('\n')

file.close()