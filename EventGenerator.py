#############################################################################################
#Event Generator that generates event files from a template. The template values are defaults
#that can be overridden by supplying flag pairs to the command line through the -f flag.
#An optional --ForecastStart argument makes the script create an event file to follow the first one.
#The non forecast event file (Event.evt) will assume that there is another event to follow 
#starting today. 
#############################################################################################

import os
import argparse
import datetime

class args(object):
  pass
#define some helper functions

#returns a DateTime object from a string input (used to parse the command line argument)
def buildDateTime (input):
    return datetime.datetime.strptime(input, '%Y/%m/%d').date()
  
#Get command line arguments
data = args()
parser = argparse.ArgumentParser()
parser.add_argument('YearStart', type=buildDateTime , help='format: yyyy/mm/dd')
parser.add_argument('-FS', '--ForecastStart', type=buildDateTime , help='format: yyyy/mm/dd')
parser.add_argument('-f', '--flag', action='append', nargs=2, help='A flag value pair. Will override the default in the template file. Ex: -f :flag val -f :anotherflag anotherval')
parser.add_argument('-fd', '--ForecastDates', help='a set of dates of format yyyy/mm/dd signifying the dates to follow')
parser.add_argument('-spinup','--Spinup',help='used to correctly create spinup event files. used only in subsequent calls after inital event.evt created.')
parser.parse_args(namespace=data)

#initialize useful variables
Path = os.path.split(os.path.abspath(__file__))[0]

#parse ForecastDates (events to follow)
if data.ForecastDates.strip(): #don't parse if empty
  ParsedForecastDates = data.ForecastDates.split(" ")
  ParsedForecastDates = [datetime.datetime.strptime(s,"%Y/%m/%d") for s in ParsedForecastDates]
else:
  ParsedForecastDates = " "

#Check if creating a forecast event or a historical event
if data.ForecastStart is None:
    date = data.YearStart
else:
    date = data.ForecastStart

#Go through Template file replacing everything that needs to be replaced
Infile = open(Path + '/../lib/TEMPLATE.evt', 'rb')
table = [row.strip().split() for row in Infile]
for i, line in enumerate(table):
    #check for empty line
    if len(line) == 0:
        continue
        
    #fix the initial date data
    elif line[0] == ':year':
        table[i][1] = date.strftime('%Y')
    elif line[0] == ':month':
        table[i][1] = date.strftime('%m')
    elif line[0] == ':day':
        table[i][1] = date.strftime('%d')
    elif line[0] == ':hour':
        table[i][1] = '00'
    
	
    #set correct file names for met and tem data
    elif line[0] == ':streamflowdatafile':
        table[i][1] = table[i][1].replace('YYYYMMDD', date.strftime('%Y%m%d'))
    elif line[0] == ':reservoirreleasefile':
        table[i][1] = table[i][1].replace('YYYYMMDD', date.strftime('%Y%m%d'))
    elif line[0] == ':reservoirinflowfile':
        table[i][1] = table[i][1].replace('YYYYMMDD', date.strftime('%Y%m%d'))
    elif line[0] == ':griddedrainfile':
        table[i][1] = table[i][1].replace('YYYYMMDD', date.strftime('%Y%m%d'))
    elif line[0] == ':griddedtemperaturefile':
        table[i][1] = table[i][1].replace('YYYYMMDD', date.strftime('%Y%m%d'))
    elif line[0] == ':diversionflowfile':
        table[i][1] = table[i][1].replace('YYYYMMDD', date.strftime('%Y%m%d'))
    
    #set events to follow if historical event
    elif line[0] == ':noeventstofollow':
        if date == data.YearStart:
            table[i][1] = len(ParsedForecastDates)
            for j in range (0,len(ParsedForecastDates)):
                table.insert(i+j+2, ['event\\' + ParsedForecastDates[j].strftime('%Y%m%d') + '.evt'])
        else:
            table[i][1] = 0
    
    #set correct file names for everything else
    else:
        if len(line) > 1:
            table[i][1] = table[i][1].replace('YYYYMMDD', data.YearStart.strftime('%Y%m%d'))
    
    #set flag overrides from command line arguments
    if data.flag is not None:
        for flagPair in data.flag:
            if line[0] == flagPair[0]:
                table[i][1] = flagPair[1]
    


#check what kind of event file we're writing (historical or forecast) and write appropriate file name
if date == data.YearStart and data.Spinup == "True":
	# creating successive event files for spin up
	file = open(Path + '/../wpegr/event/' +  date.strftime('%Y%m%d') + '.evt', 'w')
elif date == data.YearStart or data.ForecastStart is not None:
    file = open(Path + '/../wpegr/event/event.evt', 'w')
else:
    file = open(Path + '/../wpegr/event/' +  date.strftime('%Y%m%d') + '.evt', 'w')
 
#write file
for i, line in enumerate(table):
    for j, val in enumerate(line):
        if j is 0:
			file.write(str(val.ljust(40)))
        else:
            file.write(str(val) + " ")
    file.write('\n')
    
    
    