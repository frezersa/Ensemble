import pyEnSim.pyEnSim as pyEnSim


def load_r2c_template(r2cpath):
    """
    loads the attributes of an r2c template
    
    Args:
    path of single frame r2c file
    
    Returns:
    pyEnSim object
    """
    r2c_template = pyEnSim.CRect2DCell()
    r2c_template.SetFullFileName(r2cpath)
    r2c_template.LoadFromFile()
    r2c_template.InitAttributes()
    
    return r2c_template
    
    
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
    
    
    
def grib_save_r2c(grib_object,r2c_template_object,FileName):
    """
    converts a single grib file to an r2c file. A template file must be given the grib data
    is interpolated onto the template grid (not sure what interpolation technique is used but
    it seems fairly robust)
    
    Args:
        grib_object:
        r2c_template:
        FileName:
    Returns:
        NULL
    """
    #create a new r2c object based on template
    r2c_object = r2c_template_object

    #get  data from the grib object
    gribdata = grib_object.GetChild(0)
    cs = grid.GetCoordinateSystem()
    
    #transfer grib data onto the r2c object
    r2c_object.ConvertToCoordinateSystem(cs)
    r2c_object.MapObjectDispatch(grid)
    r2c_object.SetCurrentFrameCounter(1)
    
    # timestamp not currently used but available
    # timeStamp.Set(date.year,date.month,date.day,date.hour,0,0,0)
    # dest.SetCurrentStepTime(timeStamp)
    
    #save to file
    r2c_object.SaveToMultiFrameASCIIFile(FileName,0)
    
    
    
    
grib_object = load_grib_file("Q:\WR_Ensemble_dev\A_MS\Repo\scripts\NOMAD.grib2")
r2c_template_object = load_r2c_template("Q:\WR_Ensemble_dev\A_MS\Repo\lib\EmptyGridLL.r2c")
grib_save_r2c(grib_object, r2c_template_object, "testr2c.r2c")





