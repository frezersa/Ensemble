import os
import datetime
import pprint
import math



#returns a DateTime object from a string input (used to parse the command line argument)
def buildDateTime (input):
    return datetime.datetime.strptime(input, '%Y/%m/%d').date()
    

 
#returns a Time object from a string input (used to parse the command line argument) 
def buildTime (input):
  return datetime.datetime.strptime(input + ":00:00", "%H:%M:%S").time()
  
  
def ResInflowGenerator(config_file, template_name, start_date, NumDays = 10):
    """
    
    """
    #initialize useful variables
    repo_path = config_file.repository_directory
    
    file = open(os.path.join(repo_path,"lib",template_name),'rb')
    table = [row.strip().split() for row in file]
    
    start_date = datetime.datetime.strptime(start_date,"%Y/%m/%d")
    suffix =  template_name.split('_')[1]
    
    
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
            HeaderData[i][1] = start_date.strftime("%Y/%m/%d")
            
        elif line[0] == ':StartTime':
            HeaderData[i][1] = start_date.strftime("%H:%M:%S")
            
        #get the number of stations
        elif line[0] == ':ColumnName':
            numStations = len(line) - 1

            
    # write tb0 file
    file = open(os.path.join(config_file.model_directory_path, "resrl", start_date.strftime("%Y%m%d") + '_rin.tb0'), 'w')

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
    
    
        
  
  
def StreamFlowGenerator(config_file, template_name, start_date, NumDays = 10):
    """
    """

    #initialize useful variables
    repo_path = config_file.repository_directory
    
    file = open(os.path.join(repo_path,"lib",template_name),'rb')
    table = [row.strip().split() for row in file]
    
    start_date = datetime.datetime.strptime(start_date,"%Y/%m/%d")
    suffix =  template_name.split('_')[1]
  

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
            HeaderData[i][1] = start_date.strftime("%Y/%m/%d")
            
        elif line[0] == ':StartTime':
            HeaderData[i][1] = start_date.strftime("%H:%M:%S")
            
        #get the number of stations
        elif line[0] == ':ColumnName':
            numStations = len(line) - 1

            
    # write tb0 file
    file = open(os.path.join(config_file.model_directory_path, "strfw", start_date.strftime("%Y%m%d") + '_str.tb0'), 'w')


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






    
    
    
    
def EventGenerator(config_file, start_date, first_event = True, events_to_follow = False, flags = False):
    """
    Event Generator that generates event files from a template. The template values are defaults
    that can be overridden by supplying flag pairs to the command line through the flags.
    
    Args:
        config_file: specific class used for framework input, see FrameworkLibrary.py Class ConfigParse
        start_date: string specifying start date of event file. Required. Format is "YYYY/MM/DD"
        first_event: True or False. True will name the output event.evt and ensure any events_to_follow are correctly specified
        events_to_follow: False or a list of strings giving the event names. Event names must be in format ["YYYYMMDD.evt","YYYYMMDD.evt",...]
        flags: pairs in a list. The first value specifies the flag to match in the event file, the second value is what to substitute in behind the flag
                format must be False, or a list within a list.
                ex) [[":tbcflg","y"],[":pointsoilmoisture","pathtofile"]]
                
    Output: writes an event file to the event directory, as specified in the config_file
    
    
    
    """


    #initialize useful variables
    repo_path = config_file.repository_directory
    
    start_date = datetime.datetime.strptime(start_date,"%Y/%m/%d")
    
    if events_to_follow is not False:
        #events_to_follow = events_to_follow.split(",")
        events_to_follow = [datetime.datetime.strptime(s,"%Y%m%d.evt") for s in events_to_follow]




    #Go through Template file replacing everything that needs to be replaced
    Infile = open(os.path.join(repo_path,"lib","TEMPLATE.evt"), 'rb')
    table = [row.strip().split() for row in Infile]
    for i, line in enumerate(table):
        #check for empty line
        if len(line) == 0:
            continue
            
        #fix the initial date data
        elif line[0] == ':year':
            line[1] = start_date.strftime('%Y')
        elif line[0] == ':month':
            line[1] = start_date.strftime('%m')
        elif line[0] == ':day':
            line[1] = start_date.strftime('%d')
        elif line[0] == ':hour':
            line[1] = '00'
            
        #set events to follow if stitching events together
        elif line[0] == ':noeventstofollow':
            if first_event is True and events_to_follow is not False:
                line[1] = len(events_to_follow)
                for j in range (0,len(events_to_follow)):
                    table.insert(i+j+2, ['event\\' + events_to_follow[j].strftime('%Y%m%d') + '.evt'])
            else:
                line[1] = 0
        
        
        #swap any file references to include actual start date
        if len(line) > 1:
            try: #this only works if you feed it a string, ignore if not a string
                line[1] = line[1].replace('YYYYMMDD', start_date.strftime('%Y%m%d'))
            except:
                pass

        
        #set flag overrides from command line arguments
        if flags is not False:
            for flagPair in flags:
                if line[0] == flagPair[0]:
                    line[1] = flagPair[1]
    


    #check what kind of event file we're writing (historical or forecast) and write appropriate file name
    if first_event:
        file = open(os.path.join(repo_path,config_file.model_directory,'event','event.evt'), 'w') 
    else:
        file = open(os.path.join(repo_path,config_file.model_directory,'event',start_date.strftime('%Y%m%d') + '.evt'), 'w')
     
    #write file
    for i, line in enumerate(table):
        for j, val in enumerate(line):
            if j is 0:
                file.write(str(val.ljust(40)))
            else:
                file.write(str(val) + " ")
        file.write('\n')
    file.close()
    
    
    
    
    
#############################################################################################
# generic tb0 template writter. takes template file, date in YYYY/MM/DD, directory to write file to & file suffix (_ill.pt2)
#############################################################################################

def GenericTemplateWriter(config_file, template_name, start_date):

    #initialize useful variables
    repo_path = config_file.repository_directory
    
    file = open(os.path.join(repo_path,"lib",template_name),'rb')
    table = [row.strip().split() for row in file]
    
    start_date = datetime.datetime.strptime(start_date,"%Y/%m/%d")
    suffix =  template_name.split('_')[1]
   
    
    #build new table from Template
    #NOTE: ColumnName MUST come before the coefficients in the TEMPLATE file    
    indices = []
    for i, line in enumerate(table):
        #fix some of the meta data
        if line[0] == ':CreationDate':
            table[i][1] = datetime.datetime.now().strftime("%Y-%m-%d")
            table[i][2] = datetime.datetime.now().strftime("%H:%M")
        
        if line[0] == ':StartDate':
            table[i][1] = start_date.strftime("%Y/%m/%d")
        
        if line[0] == ':StartTime':
            table[i][1] = start_date.strftime("%H:%M:%S")


    #figure out where to write the output
    if suffix == "crs.pt2":
        write_directory = "snow1"
    if suffix == "div.tb0":
        write_directory = "diver"
    if suffix == "gsm.r2c":
        write_directory = "moist"
    if suffix == "ill.pt2":
        write_directory = "level"
    if suffix == "psm.pt2":
        write_directory = "moist"
    if suffix == "rel.tb0":
        write_directory = "resrl"
    if suffix == "rin.tb0":
        write_directory = "resrl"
    if suffix == "str.tb0":
        write_directory = "strfw"
    if suffix == "swe.r2c":
        write_directory = "snow1"
        
        
        

    # write tb0 file
    file = open(os.path.join(config_file.model_directory_path,write_directory,start_date.strftime("%Y%m%d") + "_" + suffix), 'w')

    #output the new data    
    for i, line in enumerate(table):   
        for j, val in enumerate(line):
            if j is 0:
                file.write(str(val.ljust(20))),
            else:
                file.write(str(val.rjust(15))),
        file.write("\n")

    file.close()



  


