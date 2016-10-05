"""
Library of functions that utilize pyEnSim capabilities. This module was written because the 
forecasting framework has a few specific tasks that require pyEnSim, and because there is 
no documentation for the pyEnSim library.
"""

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
    
    
    
def grib_save_r2c(grib_path, r2c_template_path, r2cTargetFilePath, timestamp = datetime.datetime.now(), convert_mult = False, convert_add = False, ensemble = False):
    """
    converts a single grib file to an r2c file. A template file must be given the grib data
    is interpolated onto the template grid (not sure what interpolation technique is used but
    it seems fairly robust)
    
    Args:
        grib_path: full path to where the grib file is stored
        r2c_template_path: full path to where the r2c template is stored.
        r2cTargetFilePath: full path to where the new r2c should be created
        timestamp: date and time of first frame of r2c. Defaults to current day at hour 0 if no value given
        convert_mult: either 'False' (python defined, not a string), or a number. If not False, then the number will be multiplied to each gridpoint. Negatives are allowed. Typically used to convert metres to millimetres.
        convert_add: either 'False' (python defined, not a string), or a number. If not False, then the number will be added to each gridpoint. Negatives are allowed. Typically used to convert Kelvin to Celcius
        ensemble: either 'False' (python defined, not a string), or a integer. If not False, then the same number of r2c files will be created from the 'children' of the grib file. If the integer is greater than
                    the number of children, the number of children will be used instead. This is used for the EC datamart grib files in which each ensemble is a 'child' in the main file (unlike the NOMADS format,
                    where every ensemble has its own separate grib file)
        
    Returns:
        NULL - outputs r2c file(s)
    """
    #get  data from the grib object
    grib_object = load_grib_file(grib_path)
    
    #if using the ensemble option (ie. ensembles are in the children of the grib file)
    #then set the number of ensembles, else default to 1
    if ensemble is not False:
        rasterCount = min(grib_object.GetChildrenCount(),ensemble)
        
        #also get the base name of the r2c file so that we can append an ensemble number to it
        regexp = re.compile("\d\d.r2c")
        if regexp.search(r2cTargetFilePath) is not None:
            r2cTargetFilePathbase = re.split("\d\d.r2c",r2cTargetFilePath)[0] #remove the last digits and suffix from the file name, to be added later
        else:
            r2cTargetFilePathbase = re.split(".r2c",r2cTargetFilePath)[0] #if the pattern can't be found, then just remove the .r2c suffix  
    else:
        rasterCount = 1

    
    #get the r2c object and its attributes
    r2c_object = load_r2c_template(r2c_template_path)
    cs = r2c_object.GetCoordinateSystem()  

    
    for i in range(0,rasterCount):   
        if ensemble is not False:   
            r2cTargetFilePath = r2cTargetFilePathbase + "%02d" % (i+1) + ".r2c" #append ensemble num and suffix
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
        r2c_object.SaveToMultiFrameASCIIFile(r2cTargetFilePath,0)
        
    
   
def grib_fastappend_r2c(grib_path, template_r2c_object, r2cTargetFilePath, frameindex, frametime, convert_mult = False, convert_add = False, ensemble = False, grib_previous = False):
    """
    converts a single grib file and appends to an r2c file. A template file must be given so the grib data
    is interpolated onto the template grid (not sure what interpolation technique is used but
    it seems fairly robust). The template must have the same attributes as the target file. Unfortunately
    the target attributes cannot be extracted without a time consuming conversion to binary (hence why
    the small tamplate file is required)
    
    Args:
        grib_path: full path to where the grib file is stored
        template_r2c_object: r2c template object, this is loaded outside of the function because it is
                            only needed once, while the function is used repeatedly
        r2cTargetFilePath: full path to where the new r2c should be created
        frameindex: integer for what to label the frame index
        frametime: datetime object - used to datestamp the frame
        convert_mult: either 'False' (python defined, not a string), or a number. If not False, then the number will be multiplied to each gridpoint. Negatives are allowed. Typically used to convert metres to millimetres.
        convert_add: either 'False' (python defined, not a string), or a number. If not False, then the number will be added to each gridpoint. Negatives are allowed. Typically used to convert Kelvin to Celcius
        ensemble: either 'False' (python defined, not a string), or a integer. If not False, then the same number of r2c files will be created from the 'children' of the grib file. If the integer is greater than
                    the number of children, the number of children will be used instead. This is used for the EC datamart grib files in which each ensemble is a 'child' in the main file (unlike the NOMADS format,
                    where every ensemble has its own separate grib file)
        grib_previous: either 'False' (python defind, not a string), or a path to a preceding grib file. If that path is given, this grib file will be loaded and subtracted from the target grib file. This is used
                        for accumulated precipitation. (ie. grib2 - grib1 = the precipitation that fell between the time2 and time1)

    Returns:
        NULL
    """
    
    #get data from the grib object
    grib_object = load_grib_file(grib_path)
    
    if ensemble is not False:
        rasterCount = min(grib_object.GetChildrenCount(),ensemble)
        
    else:
        rasterCount = 1
    r2cTargetFilePathbase = re.split("\d\d.r2c",r2cTargetFilePath)[0] #remove the last digits and suffix from the file name, to be added later
        
    for i in range(0,rasterCount):
        #rename r2c file if ensemble, otherwise keep original name
        if ensemble is not False:
            r2cTargetFilePath = r2cTargetFilePathbase + "%02d" % (i+1) + ".r2c"
        else:
            pass

        #load the grib object
        firstRaster = grib_object.GetChild(i)
        firstRaster.InitAttributes()
        finalRaster = firstRaster
        
        #subtract the previous grib file from the target grib file, if specified in function arguments
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
        template_r2c_object.AppendToMultiFrameASCIIFile(r2cTargetFilePath,0)    
        
        


    
def r2c_EndFrameData(r2cTargetFilePath):
    """
    Given a path to an ascii r2c file, it returns the last frame number and frame time
    
    Args:
        r2cTargetFilePath: full path to an ascii r2c
        
    Returns:
        lastindexframe: an integer denoting the number of the last frame
        endtimeframe: a datetime object denoting the timestamp of the last frame
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
        
    return lastindexframe, endtimeframe
    

