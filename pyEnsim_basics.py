import pyEnSim.pyEnSim as pyEnSim
import re
import datetime


def load_r2c_template(r2cpath):
    """
    loads the attributes of an r2c template
    
    Args:
    path of single frame r2c file
    
    Returns:
    pyEnSim object
    """
    r2c_object = pyEnSim.CRect2DCell()
    r2c_object.SetFullFileName(r2cpath)
    r2c_object.LoadFromFile()
    r2c_object.InitAttributes()
        
    return r2c_object
    
    
def load_grib_file(grib_path):
    """
    loads a grib file
    
    Args:
        grib_path: path of a grib2 file
    Returns:
        pyensim object
    """
    
    GribFile = pyEnSim.CGrib2File()
    GribFile.SetFullFileName(grib_path)
    GribFile.LoadFromFile()
    GribFile.InitAttributes()

    
    return GribFile
    
    
    
def grib_save_r2c(grib_path, r2c_template_path, r2cTargetFileName, timestamp = datetime.datetime.now(), convert_mult = False, convert_add = False, ensemble = False):
    """
    converts a single grib file to an r2c file. A template file must be given the grib data
    is interpolated onto the template grid (not sure what interpolation technique is used but
    it seems fairly robust)
    
    Args:
        grib_object:
        r2c_template:
        FileName:
        timestamp: date and time of first frame of r2c. Defaults to current day at hour 0 if no value given
    Returns:
        NULL
    """
   #get  data from the grib object
    grib_object = load_grib_file(grib_path)
    
    if ensemble is not False:
        rasterCount = min(grib_object.GetChildrenCount(),ensemble)
    else:
        rasterCount = 1
    r2cTargetFileNamebase = re.split("\d\d.r2c",r2cTargetFileName)[0] #remove the last digits and suffix from the file name, to be added later
    # print r2cTargetFileName
    # print r2cTargetFileNamebase
    
    #get the r2c object and its attributes
    r2c_object = load_r2c_template(r2c_template_path)
    cs = r2c_object.GetCoordinateSystem()  

    
    for i in range(0,rasterCount):
        print "rastercount" + str(i)
        
        if ensemble is not False:   
            r2cTargetFileName = r2cTargetFileNamebase + "%02d" % (i+1) + ".r2c"
        else:
            pass
            
        firstRaster = grib_object.GetChild(i)
        firstRaster.InitAttributes()
        
        #apply unit converstions
        if convert_add != False:
            #print firstRaster.GetNodeCount()
            for k in range(0,firstRaster.GetNodeCount()):
                #print firstRaster.GetNodeValue(k)
                firstRaster.SetNodeValue(k, firstRaster.GetNodeValue(k) + convert_add)
                
        if convert_mult != False:
            for k in range(0,firstRaster.GetNodeCount()):
                firstRaster.SetNodeValue(k, firstRaster.GetNodeValue(k) * convert_mult)
        
        #convert grib object to r2c attributes
        firstRaster.ConvertToCoordinateSystem(cs)
        
        #set time
        timeStep = pyEnSim.CEnSimDateTime()
        timeStep.Set(timestamp.year, timestamp.month, timestamp.day, 0, 0, 0, 0)
        
        #copy data over
        r2c_object.MapObjectDispatch(firstRaster)
        r2c_object.SetCurrentFrameCounter(1)
        r2c_object.SetCurrentStep(1)
        r2c_object.SetCurrentStepTime(timeStep)
        
        #Save to file
        r2c_object.SaveToMultiFrameASCIIFile(r2cTargetFileName,0)
        
    
   
def grib_fastappend_r2c(grib_path, template_r2c_object, r2cTargetFileName, frameindex, frametime, convert_mult = False, convert_add = False, ensemble = False, grib_previous = False):
    """
    converts a single grib file and appends to an r2c file. A template file must be given so the grib data
    is interpolated onto the template grid (not sure what interpolation technique is used but
    it seems fairly robust). The template must have the same attributes as the target file. Unfortunately
    the target attributes cannot be extracted without a time consuming conversion to binary (hence why
    the small tamplate file is required)
    
    Args:
        grib_object: a single frame object, if multiple frames, the function only used the first one
        r2c_template: template must have same attributes as the target r2c
        r2cTargetFileName: location of the r2c file that you want to append the new data to
        timeDelta: the time step you want for the new frame
    Returns:
        NULL
    """
    
    #get data from the grib object
    grib_object = load_grib_file(grib_path)
    
    if ensemble is not False:
        rasterCount = min(grib_object.GetChildrenCount(),ensemble)
        
    else:
        rasterCount = 1
    r2cTargetFileNamebase = re.split("\d\d.r2c",r2cTargetFileName)[0] #remove the last digits and suffix from the file name, to be added later
        
    for i in range(0,rasterCount):
        if ensemble is not False:
            r2cTargetFileName = r2cTargetFileNamebase + "%02d" % (i+1) + ".r2c"
        else:
            pass

        firstRaster = grib_object.GetChild(i)
        firstRaster.InitAttributes()
        finalRaster = firstRaster
        
        if grib_previous is not False:
            grib_previous_object = load_grib_file(grib_previous)
            previousRaster = grib_previous_object.GetChild(i)
            previousRaster.InitAttributes()
            
            
            for k in range(0, firstRaster.GetNodeCount()+1):
                rainvalue = firstRaster.GetNodeValue(k) - previousRaster.GetNodeValue(k)
                if rainvalue < 0:
                    rainvalue = 0
                finalRaster.SetNodeValue(k, rainvalue)
                
            

        
        #apply unit converstions
        if convert_add != False:
            for k in range(0,finalRaster.GetNodeCount()):
                finalRaster.SetNodeValue(k, (finalRaster.GetNodeValue(k) + convert_add))
                
        if convert_mult != False:
            for k in range(0,finalRaster.GetNodeCount()):
                finalRaster.SetNodeValue(k, finalRaster.GetNodeValue(k) * convert_mult)
        
        #convert grib object to r2c attributes
        cs = template_r2c_object.GetCoordinateSystem() 
        finalRaster.ConvertToCoordinateSystem(cs)
        
        
        #convert time into pyEnSim format
        timeStep = pyEnSim.CEnSimDateTime()
        timeStep.Set(frametime.year, frametime.month, frametime.day, frametime.hour, 0, 0, 0)

        
        #copy data over
        template_r2c_object.MapObjectDispatch(finalRaster)
        template_r2c_object.SetCurrentFrameCounter(frameindex)
        template_r2c_object.SetCurrentStep(frameindex)
        template_r2c_object.SetCurrentStepTime(timeStep)
        
        #Save to file
        template_r2c_object.AppendToMultiFrameASCIIFile(r2cTargetFileName,0)    
        
        


    
def r2c_EndFrameData(r2cTargetFilePath):
    """
    given a path to an ascii r2c file, it returns the last frame number and frame time
    """
    
    #get the frame and time data from the target r2c file
    match = re.findall(r':Frame\s+(\d+)\s+\d+\s+(.+)', open(r2cTargetFilePath).read())
    match = match[len(match)-1]
    lastindexframe = int(match[0])
    lasttimeframe = match[1]
    #get the timestamp from the last frame, try multiple formats
    try:
        endtimeframe = datetime.datetime.strptime(lasttimeframe, '"%Y/%m/%d %H:%M"')
    except:
        endtimeframe = datetime.datetime.strptime(lasttimeframe, '"%Y/%m/%d %H:%M:00.000"')
        
    return lastindexframe,endtimeframe
    

def grib_append_r2c(grib_path, r2c_template_path, r2cTargetFileName, timeDelta, convert_mult = False, convert_add = False, ensemble = 0):
    """
    converts a single grib file and appends to an r2c file. A template file must be given so the grib data
    is interpolated onto the template grid (not sure what interpolation technique is used but
    it seems fairly robust). The template must have the same attributes as the target file. Unfortunately
    the target attributes cannot be extracted without a time consuming conversion to binary (hence why
    the small tamplate file is required)
    
    Args:
        grib_object: a single frame object, if multiple frames, the function only used the first one
        r2c_template: template must have same attributes as the target r2c
        r2cTargetFileName: location of the r2c file that you want to append the new data to
        timeDelta: the time step you want for the new frame
    Returns:
        NULL
    """
    
    
    
    #get the r2c template object and its attributes
    r2c_object = load_r2c_template(r2c_template_path)
    cs = r2c_object.GetCoordinateSystem()  

    #get data from the grib object
    grib_object = load_grib_file(grib_path)
    firstRaster = grib_object.GetChild(ensemble)
    firstRaster.InitAttributes()
    
    #apply unit converstions
    if convert_add != False:
        for k in range(0,firstRaster.GetNodeCount()):
            firstRaster.SetNodeValue(k, (firstRaster.GetNodeValue(k) + convert_add))
            
    if convert_mult != False:
        for k in range(0,firstRaster.GetNodeCount()):
            firstRaster.SetNodeValue(k, firstRaster.GetNodeValue(k) * convert_mult)
    
    #convert grib object to r2c attributes
    firstRaster.ConvertToCoordinateSystem(cs)
    
    #get the frame and time data from the target r2c file
    lastindexframe, endtimeframe = r2c_EndFrameData(r2cTargetFileName)
    newtime = endtimeframe + datetime.timedelta(hours=timeDelta)
    
    #convert time into pyEnSim format
    timeStep = pyEnSim.CEnSimDateTime()
    timeStep.Set(newtime.year, newtime.month, newtime.day, newtime.hour, 0, 0, 0)

    
    #copy data over
    r2c_object.MapObjectDispatch(firstRaster)
    r2c_object.SetCurrentFrameCounter(lastindexframe+1)
    r2c_object.SetCurrentStep(lastindexframe+1)
    r2c_object.SetCurrentStepTime(timeStep)
    
    #Save to file
    r2c_object.AppendToMultiFrameASCIIFile(r2cTargetFileName,0)    
    
 
    
   
