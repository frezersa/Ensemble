#############################
#
#   libHyrdoBenchmark.R
#
#############################
#
#	library used to support the benchmarking routines for CHYMS
#
#
#############################
#
#
#############################

source("rlib/libXML.r")
source("rlib/libUBCWM_IO.r")
source("rlib/libENSIM_IO.r")
source("rlib/libRAVEN_IO.r")

BenchObsFlowTS <- function(file.xml) {
  # BenchObsFlowTS
  # routine that returns a timeseries of observed flow
  # uses the file.xml node (from the benchmark watershed) to determine the file type and location
  # and how to parse the file
  
  x <- BenchTS(file.xml, observed=T)
  
}


BenchEstFlowTS <- function(file.xml) {
  # BenchEstFlowTS
  # routine that returns a timeseries of observed flow
  # uses the file.xml node (from the benchmark watershed) to determine the file type and location
  # and how to parse the file
  
  x<- BenchTS(file.xml, observed=F)
  
}

BenchTS <- function(file.xml, observed=F) {
  #get time series data for the benchmarking routines
  
  attrs <- xmlAttrs(file.xml)
  filetype <- attrs["filetype"]
  file.name <- xmlValue(file.xml)
  filetype <- tolower(filetype)
  
  if (filetype=="adc") {
    
    adc <- ADC_Read(file.name)
    
    if(observed){      
      ts <- xts(adc[,"obs.flow"], adc[,"date"])
    }else{      
      ts <- xts(adc[,"calc.flow"], adc[,"date"])  
    }
    
  } else if(filetype=="ts3"){    
    ts3 <- ReadTS3(file.name)
    ts <- ts3$timeseries
    
  } else if(filetype=="tb0"){    
    tb0 <- ReadTB0(file.name)
    
    val.str <- attrs["valueCol"]
    date.str <- attrs["dateCol"]
    
    ts <- xts(tb0$data.table[,val.str], tb0$date.time)
    colnames(ts) <- c(val.str)
    
    
  } else {  
    stop(paste("BenchTS: file type not recognised ", filetype, sep=""))
    
  }
  
  return.ts <- ts
  
}


BenchWshedDetails <- function(file.xml){
    
  attrs <- xmlAttrs(file.xml)
  filetype <- attrs["filetype"]
  file.name <- xmlValue(file.xml)
  filetype <- tolower(filetype)
  
  #drainage area
  DA <- NULL 
  
  if (filetype=="wat"){
    # Get drainage area from WAT file  
    DA <- WAT_Read.DA(file.name)
    
  } else if(filetype=="rvh"){
    #Get drainage area from RVH file
    rvh <- RvReadRVH(file.name)
    DA <- sum(rvh$HRUs$data.table$AREA)
    
  }
  
  
  details <- list(DA=DA)
  
}

BenchPrecip <- function(file.xml){
  
  attrs <- xmlAttrs(file.xml)
  filetype <- attrs["filetype"]
  file.name <- xmlValue(file.xml)
  filetype <- tolower(filetype)
  
  
  if (filetype=="adc") {
    
    adc <- ADC_Read(file.name)
    
    rainfall.ts <- xts(adc[,"rainfall"], adc[,"date"])
    snowfall.ts <- xts(adc[,"snowfall"], adc[,"date"])
    ts <- rainfall.ts + snowfall.ts
    
  } else if(filetype=="tb0"){
    
    tb0 <- ReadTB0(file.name)
    
    val.str <- attrs["valueCol"]
    date.str <- attrs["dateCol"]
    
    ts <- xts(tb0$data.table[,val.str], tb0$data.table[,date.str])
    colnames(ts) <- c(val.str)
    
  }
  
  return.ts <- ts
  
}