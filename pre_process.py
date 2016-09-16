import os
import argparse
import datetime



#returns a DateTime object from a string input (used to parse the command line argument)
def buildDateTime (input):
    return datetime.datetime.strptime(input, '%Y/%m/%d').date()
    
    
    
    
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

