2016-10-18
This folder contains all the code required to run the LWCB Hydrological Modelling Framework. It is composed of
code written for python and R.


Python:
I learned all my python knowledge from the book "Learning Python" by Mark Lutz. It is a thick book but has some relevant chapters that are worth reading.
The main takeaway is that the code is structured into modules, and then functions. The main script imports modules at the beginning,
and then has access to all the functions within the imported module. For example, 'Module1.py' contains a function called 'Function1';
in the main script, function1 can be accessed by:
    import Module1
    Module1.Function1(arguments)
This structure is used a lot in the framework code. Please see the module descriptions below.

*.pyc files are python's binary version of the original *.py files. *.pyc files are automatically generated so you don't need to worry about them.
All *.py files can be viewed in a text editor.

The relevant Python files are:
    LWCB_Framework_Run_Model.py
        this is the main script from where everything is run. Please read the header in the script for usage. The script
        is usually called from the file 'RunWATFLOOD.bat'. There are multiple custom python modules which support this script.
    FrameworkLibrary.py
        This is the main module used by LWCB_Framework_Run_Model.py and contains all the general functions required for the framework
        to run. When I wasn't sure which module a function should fit under, it went in this module. Note that this module also
        depends on other custom modules.
    met_process.py
        Contains functions to download grib files from the EC datamart and nomads repositories. It also converts these files to
        r2c format which is used by WATFLOOD. It relies heavily on the pyEnSim_basics module.
    pre_process.py
        Contains functions to generate 'generic' files that are required for WATFLOOD to run. 'Generic' means any file that doesn't
        require a query to the LWCB database (those are called from an R-script).
    post_process.py
        Contains functions that call R-scripts to process and plot meteorological maps, hydrographs, and csvs containing raw data
    pyEnSim_basics.py
        Contains functions used specifically for converting, saving and appending grib data to r2c files. It relies heavily on 
        pyEnSim module, which is published by NRC but isn't documented.
    Writer_hec_dss.py
        No longer in the scripts folder but is backed up on the GIThub repository. It is used to convert output to
        .dss format which is used by HECResSim. I removed it from the repo because we currently aren't using HECResSim.
        
        
        
R:
In the Modelling Framework, R code is mainly used to 1) query the LWCB database and output tb0 files, 2) pre-process r2c files if required,
3) plot meteorological maps and 4) plot hydrographs and output raw data in csv format. All of the R scripts are called via python's subprocess.call()
command.
R implements libraries act very similarly to python's modules; a library of functions is read in at the beginning of the code, giving that script access to
those functions. However, the library's prefix is not attached to each function, hence every function must have a unique name or they will be overwritten by
whatever the last imported library was.

The relevant R files are:
    Diagnostics_ForecastMaps.R
        Generates meteorological maps of forecast and hindcast temperature and precipitation data (r2c files)
    Diagnostics_HydEnsembles.R
        Processes results from each of the hydrological ensembles that have been run. Applies bias correction to forecast
        and generates hydrographs and csvs.
    Diagnostics_Reservoirs.R
        Processes results spinup, hindcast and/or forecast data for reservoirs. Plots resulting hydrographs and generates csvs.
    Diagnostics_Streams.R
        Processes results spinup, hindcast and/or forecast data for streams. Plots resulting hydrographs and generates csvs.
    LWCBtoTBO.R
        Queries the lwcb.mdb Access database and outputs *.tb0 files for reservoir releases, diversions, lake levels, 
        precip (if not using CaPA), temperature (if not using GEMTemps), reservoir inflows, and streamflows.
    TempDiff.R
        Creates a r2c file of max and min daily temperatures. This is required for the modified Hargreaves evaporation used in WATFLOOD.
        Requires a r2c temperature file with a temporal resolution < 1 day.
    r2cAdjust.R
        No longer in the scripts folder. Originally used to modify the hindcast precipitation and temperature files. Backed up on GITHub.
    LWCBtoPT2.R
        No longer in the scripts folder. Originally used to set the initial lake levels in the spinup, but irrelavent because spinup runs
        for long enough time to normalize this. Backed up on GITHub.
        