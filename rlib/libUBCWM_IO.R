#############################
#
# 	libUBCWM-IO.R
#
#############################
#
#	library used to read / write UBCWM input and output files (classic file types)
#
#	ADC_Read - read the ascii output files.
#
#############################

ADC_Read <- function (file.name) {
# ADC_Read - function read the ADC ascii UBCWM output file
#
#	Args: 	file.name - the file name (including path) to the ADC file
# 
#	Output: data.frame with the output data and appropriate labels (as indicated in CalRec_Table.csv in "res" directory
#
	#skip first line an extract the remaining data
	adc <- read.table(file.name, header=FALSE, skip=1)

	# set the variable names and apply as data.frame header
	#adc.headers <- read.table ("CalRec_Table.csv", header=TRUE, sep=",")
  
	adc.headers<- c("date", "obs.flow", "calc.flow", "err.flow", "snow.outflow", "glacial.melt", "rain.outflow", "ground.water", "solar.rad", "albedo", "area.snow.cover", "basin.aet", "basin.pet", "basin.sd", "swe", "max.temp", "min.temp", "interception", "snowfall", "rainfall", "snowmelt", "upper.gw", "deep.gw", "snow.interflow", "rainfall.interflow", 	  "snow.fast.flow", "rainfall.fast.flow")
	
	colnames(adc) <- adc.headers

	# convert date column to actual dates
	adc[,"date"] <- as.Date(adc[,"date"])
	
	#collect the first row variables (timestep and start/end dates) as stored. 
	
	#return adc data.frame
	adc

}


WAT_Read.DA <- function(file.name) {
# WAT_Read - function read the WAT ascii UBCWM output file
#
#	THIS IS CURRENLTY A HACK, BUT SHOULD BE EXPANDED TO PROVIDE FULL WAT FILE ACCESS.
#
#	Args: 	file.name - the file name (including path) to the WAT file
# 
#	Output: ?

	# read the lines in teh file
	wat.lines <- readLines(file.name)

	# Look for the line with the band areas	
	regexp <- "C0ALEM"
	area.line <- wat.lines[grepl(pattern = regexp, x = wat.lines)]

	
	area.arr <- strsplit(area.line, split=",")
	area.arr <- area.arr[[1]]
	area.length <- length(area.arr[[1]])
	areas <- suppressWarnings(as.numeric(area.arr))
	area.sum <- sum(areas, na.rm=TRUE)
	
}


ReadWAT <- function(file.name){
  
  #read the WAT file and produce list of parameter names/values
  
  pars.Watershed <- c("Date", "P0LATS", "J0TIMA", "J0TIMZ", "J0RLTA", "J0RLTZ", "J0PARR", "TSTEP")
  pars.FlowAndMet <- c("N0AESS", "AESNAME", "WSCNAME", "TICAES", "TICWSC", "LAPSER", "IGRADP", "TSNCAP")
  pars.Stations <- c("C0ELPT", "P0SREP", "P0RREP", "A0TERM", "A0FOGY", "A0SUNY", "A0EDDF")  
  pars.NumberBands <- c("N0BANS")
  pars.Bands <- c("C0ELEM", "C0ALEM", "C0TREE", "C0CANY", "C0RIEN", "C0AGLA", "C0AGOR", "C0IMPA", "I0TSTA", "I0PSTA", "P0PADJ", "I0ESTA")  
  pars.Temperature <- c("A0TLZZ", "A0TLZP", "A0PPTP", "A0TLXM", "A0TLNM", "A0TLXH", "A0TLNH", "P0TEDL", "P0TEDU")
  pars.Precip <- c("P0GRADL", "P0GRADM", "P0GRADU", "E0LMID", "E0LHI", "A0STAB")
  pars.Interception <- c("P0PINT", "P0PINX")
  pars.PrecipType <- c("P0TASR", "A0FORM")
  pars.Evap <- c("A0PELA", "A0PEFO", "R0SNET", "P0EGEN")
    
  #read all the lines
  lines <- readLines(file.name)  

  #remove the empty or comment lines  
  empty <- grepl("^$", lines)  
  lines.ne <- lines[!empty]
  
  pars.list <- list()
  
  #assemble the parameter list
  pars.list <- c(pars.list, ReadWat.Lines(lines.ne, pars.Watershed, 1))
  pars.list <- c(pars.list, ReadWat.Lines(lines.ne, pars.FlowAndMet, 1))
  pars.list <- c(pars.list, ReadWat.Lines(lines.ne, pars.Stations, pars.list$N0AESS))
  pars.list <- c(pars.list, ReadWat.Lines(lines.ne, pars.NumberBands, 1))
  pars.list <- c(pars.list, ReadWat.Lines(lines.ne, pars.Bands, pars.list$N0BANS))
  pars.list <- c(pars.list, ReadWat.Lines(lines.ne, pars.Temperature, 1))
  pars.list <- c(pars.list, ReadWat.Lines(lines.ne, pars.Precip, 1))
  pars.list <- c(pars.list, ReadWat.Lines(lines.ne, pars.PrecipType, 1))
  pars.list <- c(pars.list, ReadWat.Lines(lines.ne, pars.Evap, 1))
  
}

ReadWat.Lines <- function(lines, pars, var.dim){

  #internal function for parsing the wat file lines for a paritcular parameter and dimensionality
  
  var.list <- list()
  
  for(i in 1:length(pars)){
    
    #search all lines for the identified variable
    var.line <- lines[grepl(pattern = pars[i], x = lines)]  
    
    #split the string to extract variable (comma separated only)
    var <- strsplit(var.line, split=",")      
    
    #If the variable is not found force to NA
    if(length(var)<=0){      
      var <- rep(NA, var.dim+1)      
    }
        
    #Unlist and remove first value
    var.vec<-unlist(var)[-1]
    
    #make numeric if it's possible
    if(!is.na(as.numeric(var.vec))){
      var.vec <-as.numeric(var.vec)
    }
    
    #limit to the specified length
    var.vec <- var.vec[1:var.dim]          
    
    #assemble variable vectors into a list.    
    var.list[[ pars[i] ]] <- var.vec            
    
  }  

  return.list <- var.list
  
}

GetUbcwmPars <- function(){
  
  file.name <- "rlib/ubcwm_parameter_list.csv"
  
  ubcwm.parameter.list <- read.csv(file.name)  
  
}
  
