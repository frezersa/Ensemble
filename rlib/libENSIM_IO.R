# Functions for reading EnSIM File Types

#check and install packages if required
list.of.packages <- c("zoo","xts")
new.packages <- list.of.packages[!(list.of.packages %in% installed.packages()[,"Package"])]
if(length(new.packages)) install.packages(new.packages,repos='http://cran.us.r-project.org')

suppressWarnings(suppressMessages(library(zoo)))
suppressWarnings(suppressMessages(library(xts)))
source("rlib/libStr.R")

ReadTB0 <- function(file.name, date.format="%Y-%m-%d %H:%M:%S"){
  
  # wasteful procedure to read ALL lines to extract the header.
  lines <- readLines(file.name)
  lines.count <- length(lines)
  end.header <- grep(pattern = "EndHeader", ignore.case=T, lines)
  header.lines <- lines[1:end.header-1]  
  
  #identify TB0 Met data lines
  metadata.start <- grep(pattern = "ColumnMetaData", ignore.case=T, lines)[1]
  metadata.end <- grep(pattern = "EndColumnMetaData", ignore.case=T, lines)
  metadata.range <- c(metadata.start+1):(metadata.end-1)
  metadata.lines <- lines[metadata.range]
  
  #remove the met data from the header lines
  header.lines <- header.lines[!(index(header.lines) %in% metadata.range)]
  keywords <- ParseHeaderLines(header.lines)
  
  data <- read.table(file.name, skip=end.header)
  data.cols <- dim(data)[2]
  data.rows <- dim(data)[1]
  name.str <- levels(keywords$Name[keywords$Name])
  
  metadata <- ParseHeaderLines(metadata.lines)
  
  
  #loop through the metadata keywords and build components
  
  for (m in 1:length(metadata)){
    
    col.str <- paste(unlist(metadata[m]))
    col.names <- scan(text=col.str, what='character', quiet=TRUE) #scan to handle quotes in column titles  
        
    key <- colnames(metadata)[m]
    temp.list <- list()
    temp.list[[ key ]] <- col.names
    
    if (m==1) {      
      metadata.list <- temp.list
    }else{
      metadata.list <- c(metadata.list, temp.list)
    }  
  }
  
  colnames(data) <- metadata.list$ColumnName
  
  
  #assemble everything into a list for export
  out.list <- list(header.lines=header.lines, keywords=keywords, data.table=data, column.metadata=metadata.list)
  
  #Special consideration required if we have StartTime and/or StartDate and DeltaT specified
  # We need to build a time-series sequence and add it to the dataset as a separate data field in the list
  # (originally put it in as a new leading column -- that is now changed for increased flexibility with 
  # different tb0 file types!)
    
  if((!is.null(keywords$StartTime) || !is.null(keywords$StartDate)) && (!is.null(keywords$DeltaT))){
    
    start.date<- EnSimResolveStartDate(start.date=keywords$StartDate, start.time=keywords$StartTime, date.format=date.format)  
    delta.time <- ParseTimeToDays(keywords$DeltaT)
    
    #convert days to seconds for seq.POSIXt
    delta.time.sec <- delta.time*86400
    
    col.date.time <- seq.POSIXt(from=start.date,by=delta.time.sec, length.out=data.rows)
    
    #col.dates <- seq.Date(from=start.date,by=delta.time, length.out=data.rows)
    
    mylist <- list(date.time=col.date.time)    
    out.list <- c(out.list, mylist)  
  }
  
  return(out.list)
  
}




EnSimResolveStartDate <- function(start.date=NA, start.time=NA, date.format="%Y-%m-%d %H:%M:%S"){
    
  
  if (is.null(start.date)){start.date=NA}
  if (is.null(start.time)){start.date=NA}
  
  if(is.na(start.date) ){
    out.date <- strptime(start.time, format=date.format)
    
  }else if(is.na(start.time)){ #assume we have the whole string in start.date
    out.date <- strptime(start.date, format=date.format)
    
  } else {
    
    temp.date <- paste(start.date, start.time, sep=" ")      
    out.date <- strptime(temp.date, format=date.format)
    
  }
    
  
  return(out.date)
  
}

ReadTS3 <- function(file.name, date.format="%Y/%m/%d %H:%M:%S", is.hydat=F){
  # ReadTS3
  # Function to Read a TS3 file and convert to a list object including a timeseries.
  
  TS3 <- ReadTS(file.name, date.format=date.format, ts.type="TS3", is.hydat=is.hydat)
  
}

ReadTS2 <- function(file.name, date.format="%Y/%m/%d %H:%M:%S"){
  
  TS2 <- ReadTS(file.name, date.format=date.format, ts.type="TS2", is.hydat=F)
  
}


ReadTS4 <- function(file.name, date.format="%Y/%m/%d %H:%M:%S"){
  
  TS4 <- ReadTS(file.name, date.format=date.format, ts.type="TS4", is.hydat=F)
  
}



ReadTS <-function(file.name, date.format="%Y/%m/%d %H:%M:%S", ts.type="TS3", is.hydat=F){
  
  #Generic Read-TS function that handles TS2, TS3, TS4 file types
  
  # wasteful procedure to read ALL lines to extract the header.
  lines <- readLines(file.name)
  lines.count <- length(lines)
  end.header <- grep(pattern = "EndHeader", lines)
  header.lines <- lines[1:end.header-1]
  keywords <- ParseHeaderLines(header.lines)
  
  
    #Interrogate the DataDefinition keyword -- if it's MAGDIR or UV then we need to set the appropriate columns
  data.definition <- levels(keywords$DataDefinition[keywords$DataDefinition])
  

  
  #Strutcure the data table
  #
  #For TS3 timeseries there should only be one name (only one column)
  # unless it's a hydat and then we have to specify Column Names
  #For TS2 and TS4 and we take the names depending on the keywords
  
  name.str <- levels(keywords$Name[keywords$Name])
  if(!is.null(name.str)){
    names <- c(name.str)    
    
  } else { # if there is no name specified set it to "Value1"
    names <- c("Value1")    
  }
  
  #special handling required for UV file types
  is.UV <- F
  
  #if TS2 or TS4 we need the data definition to determine the names
  if(ts.type=="TS2"||ts.type=="TS4"){
    
    if(toupper(data.definition)=="MAGDIR"){
      names <- c("Magnitude", "Direction")
      
    } else { #data.definition == "UV"
      names <- c("U", "V")
      is.UV <-T
    }
    
  }
  
  
  if(is.hydat){ #HYDAT has a non-standard Tabular Format with the flag field not always present    
    col.names<- c("Date", "Time", "Data", "Flag")
    ts.column <- 3
    data <- read.table(file.name, skip=end.header, col.names=col.names, fill=T) #separator is whitespace by default        
  
  }else if(ts.type=="TS2") {
    col.names<- names
    ts.column <- 1
    data <- read.table(file.name, skip=end.header) #separator is whitespace by default    
  
  } else if(ts.type=="TS4"){
    col.names<- c("Date", "Time", names)
    ts.column <- 3
    data <- read.table(file.name, skip=end.header) #separator is whitespace by default    
  
  } else {
    col.names<- c("Date", "Time", names)
    ts.column <- 3
    data <- read.table(file.name, skip=end.header) #separator is whitespace by default    
  }
  
  
  #store data table dimensions and set column names
  data.cols <- dim(data)[2]
  data.rows <- dim(data)[1]  
  colnames(data)<- col.names  
  
    
  #build timeseries if not in the data-table    
  if((!is.null(keywords$StartTime) || !is.null(keywords$StartDate)) && (!is.null(keywords$DeltaT))){
    
    start.date<- EnSimResolveStartDate(start.date=keywords$StartDate, start.time=keywords$StartTime, date.format=date.format)  
    delta.time <- ParseTimeToDays(keywords$DeltaT)
    
    #convert days to seconds for seq.POSIXt
    delta.time.sec <- delta.time*86400
    
    col.date.time <- seq.POSIXt(from=start.date,by=delta.time.sec, length.out=data.rows)
  
    
  } else { #use the columns date and time to produce a postix time-series
    
    date.str <- paste(data$Date, data$Time)    
    out.date <- strptime(date.str, format=date.format)  
    col.date.time <- out.date
  }
  
  #construct default timeseries

  #for all timeseries except "UV" timeseries we use a pre-existing data column
  # but for UV we will calculate the magnitude and pass that in as the default timesers
  # called "Magnitude"
  
  #Set the name for the time-series  
  
  if (is.UV){
    ts.name <- "Magnitude"
    magnitude <- sqrt(data$U^2 + data$V^2)
    timeseries <- xts(magnitude, col.date.time)    
  }
  
  else {
    ts.name<- colnames(data)[ts.column]   
    timeseries <- xts(data[[ ts.name ]], col.date.time)
  }
    
  
  #set the timeseries name
  colnames(timeseries) <- ts.name
    
  #assemble data parsed so far into a list for export  
  out.list <- list(header.lines=header.lines, keywords=keywords, data.table=data, date.time=col.date.time, timeseries=timeseries)
  
  return(out.list)
    
}


ParseHeaderLines <- function(header.lines){
  
  header.lines <- Trim(header.lines)  #remove leading and trailing whitespace
  comments <- grepl(pattern="^#", header.lines)
  keyword.lines <- header.lines[grepl(pattern="^:", header.lines)]  
  keyword.lines <- gsub(",", " ", keyword.lines) #remove commas and replace with spaces  
  
  keyword.lines <- Trim(keyword.lines)
  spaces <- regexpr(pattern="[\\s]", keyword.lines, perl=T)
  
  #remove keywords with no values (identified with no whitespace delimeters)
  keyword.lines <- keyword.lines[!spaces<0]
  spaces <- spaces[!spaces<0]
  
  spaces <- spaces-1
  keywords <- substr(keyword.lines, 2, spaces)  #parse out the keywords 
  values <- substr(keyword.lines, spaces+1, nchar(keyword.lines)) #parse out values
  values <- gsub("(^\\s+)|(\\s+$)", "", values)  #trim leading and trailing white space
  
  values <- as.data.frame(t(values))
  colnames(values) <- keywords
    
  return(values)
    
}


ParseTimeToDays <- function(time.str){
  #return a value in Days
  
  time.str <- Trim(time.str)
  
  x<- strsplit(time.str, ":") [[1]]
  x <- as.numeric(x)
  
  factors<- c(24, 24*60, 24*60*60)
  
  
  days<-0
  for (n in 1:length(x)) {  
    days<-days + x[n]/factors[n]    
  }
  
  return.days <- days  
}