
#check and install packages if required
list.of.packages <- c("xts","RODBC","scales","gdata","RSQLite","tools","reshape2")
new.packages <- list.of.packages[!(list.of.packages %in% installed.packages()[,"Package"])]
if(length(new.packages)) install.packages(new.packages,repos='http://cran.us.r-project.org')

#Set of functions created specifically for LWCB
suppressWarnings(suppressMessages(library(xts)))
suppressWarnings(suppressMessages(library(RODBC)))
suppressWarnings(suppressMessages(library(scales)))
suppressWarnings(suppressMessages(library(gdata)))
suppressWarnings(suppressMessages(library(RSQLite)))
suppressWarnings(suppressMessages(library(tools)))
suppressWarnings(suppressMessages(library(reshape2)))
Sys.setenv(TZ="GMT") #set time zone (not sure if this is required)

hourlyquery<-function(StationNumber=71,Range="",DBSource="Z:/LWS_Db/lwcb.mdb"){
  #Function to query all of the historical data in the database
  #User inputs the station number
  #Possible Range formats: 1) "2005-05-01/"
  #                        2) "/2005-05-01"
  #                        3) "2005-05-01/2009-05-01"
  #                        4) ""
  
  
  rangestring<-unlist(strsplit(Range,"/"))
  rangestring[rangestring==""]<-"1900-01-01"
  suppressWarnings(rangestring<-as.Date(min(rangestring)))
  
  
  
  
  #Connect to Database
  LWDB<-odbcConnectAccess(DBSource)
  
  #Query the database
  Data<-sqlQuery(LWDB,paste("SELECT HourlyData.Date, HourlyData.[0:00],
    HourlyData.[1:00], HourlyData.[2:00], HourlyData.[3:00], HourlyData.[4:00], HourlyData.[5:00], HourlyData.[6:00],
    HourlyData.[7:00], HourlyData.[8:00], HourlyData.[9:00], HourlyData.[10:00], HourlyData.[11:00], HourlyData.[12:00],
    HourlyData.[13:00], HourlyData.[14:00], HourlyData.[15:00], HourlyData.[16:00], HourlyData.[17:00], HourlyData.[18:00],
    HourlyData.[19:00], HourlyData.[20:00], HourlyData.[21:00], HourlyData.[22:00], HourlyData.[23:00]
    FROM HourlyData
    WHERE (((HourlyData.StationNumber)=",StationNumber,"));"))
  
  #convert data frame in 'wide' format to 'long' format, then to a time series
  meltdata<-melt(Data,id.vars=c("Date")) 
  meltdata$datetime <- paste(meltdata$Date,meltdata$variable)
  data.ts <- xts(meltdata$value,order.by=as.POSIXct(meltdata$datetime))
  
  
  
  #Subset if required
  if(Range!=""){data.ts<-data.ts[Range]}
  
  odbcClose(LWDB)
  
  return(data.ts)
}


LWquery<-function(StationNumber=637,Range="",DBSource,useSQL=FALSE){
  #Function to query all of the historical data in the database
  #User inputs the station number
  #Possible Range formats: 1) Range <- "2015-01-01/"
  #                        2) Range <- "/2005-05-01"
  #                        3) Range <- "2005-05-01/2009-05-01"
  #                        4) Range <- ""


  
  rangestring<-unlist(strsplit(Range,"/"))
  rangestring[rangestring==""]<-"1900-01-01"

  # get start dates and end dates from Range
  if(Range==""){start_date<-as.Date("1900-01-01");end_date<-Sys.Date()}else{
    if(length(rangestring)==1){start_date<-as.Date(rangestring);end_date<-Sys.Date()}else{
     start_date<-as.Date(rangestring[1]);end_date<-as.Date(rangestring[2])}}
  
  start_date
  end_date

  suppressWarnings(rangestring<-as.Date(min(rangestring)))
  timediff<-Sys.Date()-rangestring
  
  #create empty time object for later
  dates<-seq(from=start_date,to=end_date,by=1)
  empty<-zoo(,dates)
  emptyNA<-zoo(NA,dates)

  

  #Connect to Database
  if(useSQL==TRUE){
      drv <-dbDriver("SQLite")
      LWDB<-dbConnect(drv,DBSource)
      
      #Query the 3 separate databases
      if(timediff>730||is.na(timediff)){
        DataHis<-dbGetQuery(LWDB,paste("select Value, Date from DailyDataFullRec where StationNumber =",StationNumber))
      }
      if(timediff>59||is.na(timediff)){
        Data2year<-dbGetQuery(LWDB,paste("select Value, Date from DailyData2Years where StationNumber =",StationNumber))
      }
      Data60Day<-dbGetQuery(LWDB,paste("select Value, Date from DailyData60Days where StationNumber =",StationNumber))
      
      dbDisconnect(LWDB)
  }else{
    #Connect to Database
    LWDB<-odbcConnectAccess(DBSource)
    
    #Query the 3 separate databases
    if(timediff>730||is.na(timediff)){
      DataHis<-sqlQuery(LWDB,paste("select Value, Date from DailyDataFullRec where StationNumber =",StationNumber))
    }
    if(timediff>59||is.na(timediff)){
      Data2year<-sqlQuery(LWDB,paste("select Value, Date from DailyData2Years where StationNumber =",StationNumber))
    }
    Data60Day<-sqlQuery(LWDB,paste("select Value, Date from DailyData60Days where StationNumber =",StationNumber))
    
    odbcClose(LWDB)
    
  }
  



  #Bind together

    if(exists("DataHis")){
      DataAll<-rbind(DataHis,Data2year,Data60Day)
    }else if(exists("Data2year")){
      DataAll<-rbind(Data2year,Data60Day)
    }else{
      DataAll<-Data60Day}
  

  
  
  #if the station is (-1), it means the user knows it doesn't exist in 
  #the LWCB database and is meant to be a placeholder, create a dummy date variable
  if(StationNumber>=(9000)){
    Dummy<-seq(as.Date("1986/05/01"),as.Date("1987/05/01"),by=1)
    DataAll.ts<-xts(rep(NA,length(Dummy)),Dummy)
  }else{
    #Create timeseries of actual data,if there is no data in the database, create empty dataset
    if(nrow(DataAll)>0){
      DataAll.ts<-xts(DataAll$Value,as.Date(DataAll$Date))
      DataAll.ts<-DataAll.ts[Range]
    }else{DataAll.ts<-emptyNA}
  }
  #check if the Range filtering excluded all possible non-NA values
  if(length(DataAll.ts)==0){DataAll.ts<-emptyNA}
  
  #Subset if required
  #if(Range!=""){DataAll.ts<-DataAll.ts[Range]}
  
 

  
  #Pad timeseries with NAs
  filled.DataAll.ts<-merge(DataAll.ts,empty,all=TRUE)
  


return(filled.DataAll.ts)
}




locationquery<-function(StationNumber,DBSource,useSQL=FALSE){
  #Function to query the DailyMaster table to find the latitude, longitude and elevation of a station
  

  #Connect to Database
  if(useSQL==TRUE){
    drv <-dbDriver("SQLite")
    LWDB<-dbConnect(drv,DBSource)
    
    Location<-dbGetQuery(LWDB,paste("SELECT DailyMaster.StationNumber, Locations.Longitude, Locations.Latitude, Locations.Elevation, Locations.Drainage_Area
                          FROM DailyMaster INNER JOIN Locations ON DailyMaster.Location = Locations.LocationID
                          WHERE (((DailyMaster.StationNumber)=",StationNumber,"))",sep=""))
    
    dbDisconnect(LWDB)
  }else{
    #Connect to Database
    LWDB<-odbcConnectAccess(DBSource)
    
    Location<-sqlQuery(LWDB,paste("SELECT DailyMaster.StationNumber, Locations.Longitude, Locations.Latitude, Locations.Elevation, Locations.Drainage_Area
                     FROM DailyMaster INNER JOIN Locations ON DailyMaster.Location = Locations.LocationID
                     WHERE (((DailyMaster.StationNumber)=",StationNumber,"))",sep=""))
    odbcClose(LWDB)
  }
  



  Location<-as.numeric(Location)
  names(Location)<-c("Station","Longitude","Latitude","Elevation","Drainage_Area")
  return(Location)
}


#Function to get average values in a time series
Avgtemp<-function(MaxStation=646,MinStation=638,Range,DBSource,useSQL=FALSE){
  
  #query the min max station, bind them to an average of the two (take average using rowMeans)
  Temps<-cbind(LWquery(MaxStation,Range=Range,DBSource=DBSource,useSQL=useSQL),LWquery(MinStation,Range=Range,DBSource=DBSource,useSQL=useSQL),
               rowMeans(cbind(LWquery(MaxStation,Range=Range,DBSource=DBSource,useSQL=useSQL),LWquery(MinStation,Range=Range,DBSource=DBSource,useSQL=useSQL))))
  
  #subset only the average column, name and return
  Temps<-Temps[,3]

  #Temps<-as.data.frame(Temps)
  names(Temps)<-"AvgTmp"
  return(Temps)
}

#Function to get average values in a time series
MaxMintemp<-function(MaxStation=646,MinStation=638,Range,DBSource,useSQL=FALSE){
  
  #query the min max station, bind them to an average of the two (take average using rowMeans)
  Temps<-cbind(LWquery(MaxStation,Range=Range,DBSource=DBSource,useSQL=useSQL),LWquery(MinStation,Range=Range,DBSource=DBSource,useSQL=useSQL))
  
  Temps<-as.data.frame(Temps)
  Temps$date<-rownames(Temps)
  Temps<-melt(Temps,id.vars="date")[,c(1,3)]
  Temps<-xts(Temps$value,as.Date(Temps$date))


  
  #Temps<-as.data.frame(Temps)
  names(Temps)<-"AvgTmp"
  return(Temps)
}


getYearsTS<-function(flow.ts){
  #Function to get the years in a time series
  #outputs a vector of years
  time.index <- index(flow.ts)
  years <- format(as.numeric(format(time.index, "%Y")))
  years <- unique(years) 
}



getfullTS <- function(flow.ts){
#function to remove first and last years of time series 
#if they don't contain 365 days of data
#then fill any missing values in the time series with NA
#outputs the modified time-series
  
  # Extract date index
  time.index <- index(flow.ts)
  years <- format(as.numeric(format(time.index, "%Y")))
  years <- unique(years)  
  
  
  
  #remove first and last years if they don't contain 365 days
  #if(length(flow.ts[years[1]])<365){years<-years[-1]}
  #if(length(flow.ts[years[length(years)]])<365){years<-years[-length(years)]}
  #flow.ts<-flow.ts[years]
  
  #create empty timeseries from first and last dates
  #time.index.cull <- index(flow.ts)
  dates<-seq(from=as.Date(paste(years[1],"-01-01",sep="")),to=as.Date(paste(years[length(years)],"-12-31",sep="")),by=1)
  empty<-xts(,dates)
  
  #fill the timeseries
  flow.ts<-merge(flow.ts,empty,all=TRUE)
  
  #ensure the timeseries has no extra attribute data attached to it (causes issues in period.apply()/apply.monthly())
  flow.ts<-xts(as.vector(flow.ts),dates)
  
  return(flow.ts)
}
  




q.m.mean<-function(flow.ts){
  #function to calculate the average value over each quarter week
  #outputs a matrix with 48 columns (for each quarter month in a year)
  #and the number of rows equaling the number of complete years
  
  #ensure first and last years have complete data
  flow.ts<-getfullTS(flow.ts)
  
  #define a quarter month function
  quarterfunction<-function(x){period.apply(x,c(0,8,15,22,length(x)),mean,na.rm=T)}

  #apply function over annual time series
  quartermeans<-apply.monthly(flow.ts,quarterfunction)
  
  #convert to a matrix and label the rows and columns
  quartermeans<-t(matrix(t(quartermeans),nrow=48))
  names(quartermeans)<-seq(1,48,1)
  row.names(quartermeans)<-getYearsTS(flow.ts)
  
  return(quartermeans)
}




q.m.sum<-function(flow.ts){
  #function to calculate the total value over each quarter week
  #outputs a matrix with 48 columns (for each quarter month in a year)
  #and the number of rows equaling the number of complete years
  
  #ensure first and last years have complete data
  flow.ts<-getfullTS(flow.ts)
  
  #define a quarter month function
  quartersumfunction<-function(x){period.apply(x,c(0,8,15,22,length(x)),sum)}
  
  #apply function over annual time series
  quartersums<-apply.monthly(flow.ts,quartersumfunction)
  
  #convert to a matrix and label the rows and columns
  quartersums<-t(matrix(t(quartersums),nrow=48))
  names(quartersums)<-seq(1,48,1)
  row.names(quartersums)<-getYearsTS(flow.ts)
  
  return(quartersums)
}


q.m.endmean<-function(flow.ts){
  #function to calculate the 3-day mean value at the end of quarter week
  #outputs a matrix with 48 columns (for each quarter month in a year)
  #and the number of rows equaling the number of complete years
  
  #take rolling 3 day average over whole series
  flow.ts<-rollmean(flow.ts,3,"extend")
  
  #ensure first and last years have complete data
  flow.ts<-getfullTS(flow.ts)
  
  #define a quarter month function
  endmeanfunction<-function(x){period.apply(x,c(0,8,15,22,length(x)),function(y){return(y[length(y)])})}
  
  #apply function over annual time series
  endmeans<-apply.monthly(flow.ts,endmeanfunction)
  
  #convert to a matrix and label the rows and columns
  endmeans<-t(matrix(t(endmeans),nrow=48))
  #names(endmeans)<-seq(1,48,1)
  row.names(endmeans)<-getYearsTS(flow.ts)
  
  return(endmeans)
}

Percentiles<-function(flow.matrix){
  #function to calculate the percentiles and max,min station on a matrix time series
  #outputs a matrix in the format used in the Percentiles DB table
  
  flows.stats <-t(apply(flow.matrix, 2, function(x) quantile(x,seq(1,0,-.05), na.rm=T)))
  station.max <-row.names(flow.matrix)[apply(flow.matrix,2,which.max)]
  station.min <-row.names(flow.matrix)[apply(flow.matrix,2,which.min)]
  
  flows<-data.frame(MaxYear=station.max,flows.stats,MinYear=station.min)
  
}


q.m.stats<-function(StationNumber=75,PercentileType="Discharge",MinRange="",MaxRange="",SigRange="1981/2010"){
  #function to calculate percentiles of a specified year range, and the absolute min,max of the whole year range
  #outputs a matrix in the format used in the Percentiles DB table
  
  #Get time series for both extreme and significant range
  flow.ts.min<-LWquery(StationNumber,MinRange)
  flow.ts.max<-LWquery(StationNumber,MaxRange)
  flow.ts.sig<-LWquery(StationNumber,SigRange)
  
  #calculate percentiles based on the Percentile Type specified by the user
  if(PercentileType=="Elevation"){
    MinSeries<-q.m.endmean(flow.ts.min)
    MaxSeries<-q.m.endmean(flow.ts.max)
    SigSeries<-q.m.endmean(flow.ts.sig)
  }else if(PercentileType=="Discharge"|PercentileType=="Local Inflow"|PercentileType=="Total Inflow"){
    MinSeries<-q.m.mean(flow.ts.min)
    MaxSeries<-q.m.mean(flow.ts.max)
    SigSeries<-q.m.mean(flow.ts.sig)
  }else if(PercentileType=="Precipitation"){
    MinSeries<-q.m.sum(flow.ts.min)
    MaxSeries<-q.m.sum(flow.ts.max)
    SigSeries<-q.m.sum(flow.ts.sig)
  }else{return("Error: PercentileType is incorrect")}
  
  #Calculate Percentiles of Series
  MinPerc<-Percentiles(MinSeries)
  MaxPerc<-Percentiles(MaxSeries)
  SigPerc<-Percentiles(SigSeries)
  
  #Combine the extreme and significant values into one matrix
  Output<-cbind(MaximumYear=MaxPerc[,1],Maximum=MaxPerc[,2],SigPerc[,3:21],Minimum=MinPerc[,22],MinimumYear=MinPerc[,23])
  
  return(Output)
}
  

AnnualHydrographComparePlotGG <- function(flow.all, flow.user,Title.all="All Years",Title.user = "Parital Years"){
  
  
  
  
  flow.data.obs <- AnnualFlowProfile(flow.all)
  flow.data.est <- AnnualFlowProfile(flow.user)
  
  dates <- seq(as.Date("2001-01-01"), as.Date("2001-12-31"), by="day")
  fd.1 <- as.data.frame(flow.data.obs$flow.stats)
  fd.1 <- cbind(dates, fd.1, Class=Title.all)
  fd.2 <- as.data.frame(flow.data.est$flow.stats)
  fd.2 <- cbind(dates, fd.2, Class=Title.user)
  
  fd <- rbind(fd.1, fd.2)
  
  
  p <- ggplot(data=fd) + 
    scale_color_manual(values=c("red", "blue")) +
    scale_fill_manual(values=c("red", "blue")) +
    geom_line(aes(x=dates, y=flow.median, color=Class) ) +
    geom_ribbon(aes(x=dates, ymin=flow.25, ymax=flow.75, fill=Class), alpha=0.25) + 
    scale_x_date(name="", breaks = "1 month", labels=date_format("%b")) +
    scale_y_continuous(name="Elevation (m)")
  
}

writeTB0<-function(Data,
                   
                   Projection="LATLONG",Ellipsoid="WGS84",
                   StartDate,StartTime="00:00:00.0",
                   Deltatime="24",ColumnType="float", Author="LWCB",
                   
                   Name="lakeInflows",ColumnNames="nn",ColumnUnits="uu",
                   ColumnLocationX="xx",ColumnLocationY="yy",
                   
                   ColumnLocationX1=NULL,ColumnLocationY1=NULL,
                   UnitConversion=NULL,AttributeUnits=NULL,
                   RoutingDeltaT=NULL,
                   
                   Elevation=NULL,FileName="OutputTB0", Value1=NULL,
                   coeff1=NULL,coeff2=NULL,coeff3=NULL,coeff4=NULL,coeff5=NULL
                   
                   ){
  
  #Written by James Bomhof on Aug 8,2013 - can be modified to include more metadata
  
  #Function to write data to TB0 format
  
  #Data can be in the form of a matrix or a vector. If it is in a vector, the function
  #assumes that each value corresponds to a time step. If the user wants a single time-step
  #with many variables, they should create a matrix with 1 row and multiple columns.
  
  #Optional metadata: 
  #-The user can change the StartTime,Deltatime,FileName and Author inputing them as strings
  #-The user can change the ColumnNames,ColumnUnits,ColumnType and ColumnLocations
  #by inputing them as vectors of strings (ie. c("name1","name2",etc.)). The function
  #checks to ensure the lengths of these vectors match the number of columns in the data
  
  #Count the number of columns in matrix, continue if it is matrix
  if(!is.null(dim(Data))){
    Columns<-dim(Data)[2]
    
    
    #repeat default values if not specified by user
    if(length(ColumnNames)==1){ColumnNames<-rep(ColumnNames,Columns)}
    if(length(ColumnUnits)==1){ColumnUnits<-rep(ColumnUnits,Columns)}
    if(length(ColumnType)==1){ColumnType<-rep(ColumnType,Columns)}
    if(length(ColumnLocationX)==1){ColumnLocationX<-rep(ColumnLocationX,Columns)}
    if(length(ColumnLocationY)==1){ColumnLocationY<-rep(ColumnLocationY,Columns)}
    if(length(ColumnLocationX1)==1){ColumnLocationX1<-rep(ColumnLocationX1,Columns)}
    if(length(ColumnLocationY1)==1){ColumnLocationY1<-rep(ColumnLocationY1,Columns)}
    if(length(Elevation)==1){Elevation<-rep(Elevation,Columns)}
    if(length(Value1)==1){Value1<-rep(Value1,Columns)}
    if(length(coeff1)==1){coeff1<-rep(coeff1,Columns)}
    if(length(coeff2)==1){coeff2<-rep(coeff2,Columns)}
    if(length(coeff3)==1){coeff3<-rep(coeff3,Columns)}
    if(length(coeff4)==1){coeff4<-rep(coeff4,Columns)}
    if(length(coeff5)==1){coeff5<-rep(coeff5,Columns)}
    
    
    #Check to make sure number of columns = the length of input strings, quit and return error if it doesn't
    if(Columns!=length(ColumnNames)||
         Columns!=length(ColumnUnits)||
         Columns!=length(ColumnType)||
         Columns!=length(ColumnLocationX)||
         Columns!=length(ColumnLocationY))
      {
      return("Error:One of your inputs doesn't match the number of columns in your data")
    }
  }
  
  #round header values
  ColumnLocationX<-round(ColumnLocationX,3)
  ColumnLocationY<-round(ColumnLocationY,3)
  if(!is.null(Elevation)){Elevation<-round(Elevation,2)}
  Data<-round(Data,2)
  
  
  Data<-cbind(rep("                ",nrow(Data)),Data)
  names(Data)[1]<-"                    "
  
  
  #Write header to include all of the metadata specified by the user
  header1<-c("########################################",
            ":FileType tb0  ASCII  EnSim 1.0    ",
            "#DataType               Time Series    ",
            ":Application EnSimHydrologic",
            paste(":WrittenBy",Author),
            paste(":CreationDate",Sys.time()),
            "#-----------------------------------------",
            paste(":Name",Name),
            paste(":Projection",Projection),
            paste(":Ellipsoid",Ellipsoid),
            paste(":StartDate",StartDate),
            paste(":StartTime",StartTime),
            if(!is.null(UnitConversion))paste(":UnitConversion",UnitConversion),
            if(!is.null(AttributeUnits))paste(":AttributeUnits",AttributeUnits),
            if(!is.null(RoutingDeltaT))paste(":RoutingDeltaT",RoutingDeltaT),
            if(!is.null(Deltatime))paste(":DeltaT",Deltatime),
            ":ColumnMetaData",
            "#-----------------------------------------")
  header2<-c(paste(":ColumnUnits",paste(ColumnUnits,collapse=" ")),
            paste(":ColumnType",paste(ColumnType,collapse=" ")),
            paste(":ColumnName",paste(ColumnNames,collapse=" ")),
            paste(":ColumnLocationX",paste(round(ColumnLocationX,3),collapse=" ")),
            paste(":ColumnLocationY",paste(round(ColumnLocationY,3),collapse=" ")),
            if(!is.null(ColumnLocationX1))paste(":ColumnLocationX1",paste(ColumnLocationX1,collapse=" ")),
            if(!is.null(ColumnLocationY1))paste(":ColumnLocationY1",paste(ColumnLocationY1,collapse=" ")),
            if(!is.null(coeff1))paste(":coeff1",paste(coeff1,collapse=" ")),
            if(!is.null(coeff2))paste(":coeff2",paste(coeff2,collapse=" ")),
            if(!is.null(coeff3))paste(":coeff3",paste(coeff3,collapse=" ")),
            if(!is.null(coeff4))paste(":coeff4",paste(coeff4,collapse=" ")),
            if(!is.null(coeff5))paste(":coeff5",paste(coeff5,collapse=" ")),
            if(!is.null(Value1))paste(":Value1",paste(Value1,collapse=" ")),
            if(!is.null(Elevation))paste(":Elevation",paste(Elevation,collapse=" ")))
  #convert this part of the header to a data.frame so that the columns can be equally spaced
  header2<-as.data.frame(t(as.data.frame(strsplit(header2,split= " +"))))
  row.names(header2)<-NULL
  suppressWarnings(names(header2)<-names(Data))
  
  header3<-c(":EndColumnMetaData ",
            ":endHeader")

  
  #Create full file name
  Filelink<-paste(FileName,".tb0",sep="")
  
  #Write header to the file
  write(header1, file = Filelink)
 
  #print equally spaced columns (print.to.file is a custom function in this library)
  colspace<-print.to.file(header2,Filelink)
  
  write(header3, file = Filelink,append=T)
  
  print.to.file(Data,Filelink,colspace=colspace)
    
}



# #Function to get average values in a time series
# AvgtempSQL<-function(MaxStation,MinStation,DBSource){
#   
#   #query the min max station, bind them to an average of the two (take average using rowMeans)
#   Temps<-cbind.xts(LWquerySQL(MaxStation,DBSource=DBSource),LWquerySQL(MinStation,DBSource=DBSource),
#                    rowMeans(cbind.xts(LWquerySQL(MaxStation,DBSource=DBSource),LWquery(MinStation,DBSource=DBSource))))
#   
#   #subset only the average column, name and return
#   Temps<-Temps[,3]
#   names(Temps)<-"AvgTmp"
#   return(Temps)
# }

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

stackr2c<-function(r2cfile){
  #get header data
  lines.count<-length(r2cfile)
  end.header<-grep(pattern="EndHeader",ignore.case=T,r2cfile)
  header.lines<-r2cfile[1:end.header]
  
  #find lines where new frames start and end
  frame.start <- grep(pattern=":Frame",r2cfile)
  frame.end <- grep(pattern=":EndFrame",r2cfile)
  frame.length <- frame.end[1]-frame.start[1]-1
  
  #get extents
  xorigin<-grep(pattern=":xOrigin",ignore.case=T,r2cfile)
  xmn<-as.numeric(strsplit(header.lines[xorigin], " +")[[1]][2])
  
  xcount<-grep(pattern=":xCount",ignore.case=T,r2cfile)
  xcount<-as.numeric(strsplit(header.lines[xcount], " +")[[1]][2])
  
  xdelta<-grep(pattern=":xDelta",ignore.case=T,r2cfile)
  xdelta<-as.numeric(strsplit(header.lines[xdelta], " +")[[1]][2])
  
  xmx <- xmn + xcount*xdelta
  
  
  yorigin<-grep(pattern=":yOrigin",ignore.case=T,r2cfile)
  ymn<-as.numeric(strsplit(header.lines[yorigin], " +")[[1]][2])
  
  ycount<-grep(pattern=":yCount",ignore.case=T,r2cfile)
  ycount<-as.numeric(strsplit(header.lines[ycount], " +")[[1]][2])
  
  ydelta<-grep(pattern=":yDelta",ignore.case=T,r2cfile)
  ydelta<-as.numeric(strsplit(header.lines[ydelta], " +")[[1]][2])
  
  ymx <- ymn + ycount*ydelta
  
  #transfer r2c data into a multi-frame raster object
  rr<-do.call("stack",lapply(c(1:length(frame.start)),function(i){
    #get frame header
    FrameData<-r2cfile[frame.start[i]]
    
    #get frame data and convert to new matrix
    jam<-r2cfile[(frame.start[i]+1):(frame.end[i]-1)]
    #split the strings by whitespace (JMB: I found " +" to work for this case, may need to be changed as required,
    #also needed to delete first column of NA's (hence the [,1] at the end))
    tmpframe<-matrix(as.numeric(unlist(strsplit(jam," +"))),frame.length,byrow=T)[,-1]*1 #(convert to mm)
    
    #Convert to a raster
    r <- raster(nrow=nrow(tmpframe), ncol=ncol(tmpframe),xmn=xmn,xmx=xmx,ymn=ymn,ymx=ymx)
    names(r)<-unlist(strsplit(FrameData,"\""))[2]
    r[] <- tmpframe
    
    return(r)
  })
  )
}

#function to read r2c file
readr2c<-function(r2cfile,tzdiff=0){
  #tzdiff is POSITIVE moving west Ex. if converting from EST to CST: tzdiff=1
  
  #read r2c file
  lines<-readLines(r2cfile)
  
  #get header data
  lines.count<-length(lines)
  end.header<-grep(pattern="EndHeader",ignore.case=T,lines)
  header.lines<-lines[1:end.header]
  
  #find lines where new frames start and end
  frame.start <- grep(pattern=":Frame",lines)
  frame.end <- grep(pattern=":EndFrame",lines)
  frame.length <- frame.end[1]-frame.start[1]-1
  
  i=1
  #transfer r2c data into a multi-frame raster object
  rr<-do.call("stack",lapply(c(1:length(frame.start)),function(i){
    #get frame header
    FrameData<-lines[frame.start[i]]
    
    #get frame data and convert to new matrix
    rawdata<-lines[(frame.start[i]+1):(frame.end[i]-1)]
    #split the strings by whitespace (JMB: I found " +" to work for this case, may need to be changed as required,
    tmpframe<-matrix(as.numeric(unlist(strsplit(rawdata," +"))),frame.length,byrow=T)
    tmpframe<-tmpframe[,!is.na(tmpframe[1,])] #remove any columns with NAs
    
    #Convert to a raster
    r <- raster(nrow=nrow(tmpframe), ncol=ncol(tmpframe),xmn=-96.7,xmx=-89.7,ymn=47.3,ymx=52.3)
    
    #assign date stamp, convert timezone if required
    timestamp<-unlist(strsplit(FrameData,"\""))[2]
    timestamp<-unlist(strsplit(timestamp,"\\."))[1]
    timestamp<-as.POSIXct(strptime(timestamp,"%Y/%m/%d %H:%M"),tz="GMT")
    if(tzdiff!=0) attributes(timestamp)$tzone<- paste0("GMT",tzdiff)
    
    #set raster frame
    names(r)<-format(timestamp,"%Y.%m.%d.%H.%M")
    r[] <- tmpframe
    
    return(r)
  })
  )
  
  rr<-flip(rr,'y')
  output<-list(header.lines,rr)
  return(output)
}


#function to write r2c file
writer2c<-function(header,data,FileName="default.r2c",decimal=6,frametime="days"){
  originaldata<-data
  
  data<-flip(data,'y')
  
  #Write header to the file
  writeLines(header, con = FileName)
  
  
  writeBrick<-function(i){
    if(frametime=="hours"){frame<-1+24*(i-1)}else{frame<-i}
    
    timestamp<-as.POSIXct(strptime(names(originaldata[[i]]),"X%Y.%m.%d.%H.%M"),tz="GMT")
    frameheader<-paste0(":Frame  ",frame,"   ",frame,"   \"",format(timestamp,"%Y/%m/%d %H:%M:%S"),"\"")
    framedata<-apply(as.matrix(data[[i]]),2,function(x) sprintf(paste0("%.",decimal,"f"),x,quote=F))
    frameender<-":EndFrame"
    
    #write frame header
    write(frameheader, file = FileName,append=T)
    
    #write table to the file, append=T,row.names=F,col.names=F,sep="\t" (tab deliminated)
    write.table(framedata, FileName, append=TRUE,row.names=FALSE,col.names=FALSE,sep=" ",quote=F)
    
    #write frame ender
    write(frameender, file = FileName,append=T)
    
    
  }
  
  
  
  
  invisible(lapply(c(1:nlayers(data)),writeBrick))
  
  
}

print.to.file <- function(df, filename,colspace=NA,getcolspace=FALSE) {
  cnames <- colnames(df)
  
  if(is.na(colspace[1])){
  nn<-apply(df,2,nchar)
  n <- as.matrix(apply(nn,2,max))
  }else n<-colspace
  
  d <- apply(df, 2, format)
  fmts <- paste0("%",n, "s")
  
  if(nrow(df)>1){ 
    n <- apply(cbind(n, nchar(d[1,])), 1, max)
    for(i in 1:length(cnames))
      {
      cnames[i] <- sprintf(fmts[i], cnames[i])
      d[,i] <- sprintf(fmts[i], trim(d[,i]))
      }}else{
    d<-sprintf(fmts,trim(d))
    d<-t(d)
  }
  
  if(!getcolspace){
  write.table(d, filename, quote=F, row.names=F, col.names=F,append=T)
  }
  return(n)
}

multiplot <- function(..., plotlist=NULL, file, cols=1, layout=NULL) {
  require(grid)
  
  # Make a list from the ... arguments and plotlist
  plots <- c(list(...), plotlist)
  
  numPlots = length(plots)
  
  # If layout is NULL, then use 'cols' to determine layout
  if (is.null(layout)) {
    # Make the panel
    # ncol: Number of columns of plots
    # nrow: Number of rows needed, calculated from # of cols
    layout <- matrix(seq(1, cols * ceiling(numPlots/cols)),
                     ncol = cols, nrow = ceiling(numPlots/cols))
  }
  
  if (numPlots==1) {
    print(plots[[1]])
    
  } else {
    # Set up the page
    grid.newpage()
    pushViewport(viewport(layout = grid.layout(nrow(layout), ncol(layout))))
    
    # Make each plot, in the correct location
    for (i in 1:numPlots) {
      # Get the i,j matrix positions of the regions that contain this subplot
      matchidx <- as.data.frame(which(layout == i, arr.ind = TRUE))
      
      print(plots[[i]], vp = viewport(layout.pos.row = matchidx$row,
                                      layout.pos.col = matchidx$col))
    }
  }
}



# LWquerySQL<-function(StationNumber=75,Range="",DBSource,SQL=FALSE){
#   #Function to query all of the historical data in the database
#   #User inputs the station number
#   #Possible Range formats: 1) "2015-01-01/"
#   #                        2) "/2005-05-01"
#   #                        3) "2005-05-01/2009-05-01"
#   #                        4) ""
#   
#   
#   rangestring<-unlist(strsplit(Range,"/"))
#   rangestring[rangestring==""]<-"1900-01-01"
#   suppressWarnings(rangestring<-as.Date(min(rangestring)))
#   timediff<-Sys.Date()-rangestring
#   
#   
#   
#   #Connect to Database
#   drv <-dbDriver("SQLite")
#   LWDB<-dbConnect(drv,DBSource)
#   
#   #Query the 3 separate databases
# #   if(timediff>730||is.na(timediff)){
# #     DataHis<-dbGetQuery(LWDB,paste("select Value, Date from DailyDataFullRec where StationNumber =",StationNumber))
# #   }
#   if(timediff>59||is.na(timediff)){
#     Data2year<-dbGetQuery(LWDB,paste("select Value, Date from DailyData2Years where StationNumber =",StationNumber))
#   }
#   Data60Day<-dbGetQuery(LWDB,paste("select Value, Date from DailyData60Days where StationNumber =",StationNumber))
#   
#   #Bind together
#   if(exists("DataHis")){
#     DataAll<-rbind(DataHis,Data2year,Data60Day)
#   }else if(exists("Data2year")){
#     DataAll<-rbind(Data2year,Data60Day)
#   }else{
#     DataAll<-Data60Day}
#   
#   #convert to date
#   DataAll$Date<-as.Date(DataAll$Date)
#   
#   #if the station is (-1), it means the user knows it doesn't exist in 
#   #the LWCB database and is meant to be a placeholder, create a dummy date variable
#   if(StationNumber>=(9000)){
#     Dummy<-seq(as.Date("1986/05/01"),as.Date("1987/05/01"),by=1)
#     DataAll.ts<-xts(rep(NA,length(Dummy)),Dummy)
#   }else{
#     #Create timeseries of actual data
#     DataAll.ts<-xts(DataAll$Value,DataAll$Date)
#   }
#   
#   #Subset if required
#   if(Range!=""){DataAll.ts<-DataAll.ts[Range]}
#   
#   dbDisconnect(LWDB)
#   return(DataAll.ts)
# }

#StationNumber=76
#DBSource="C:/Ensemble_Framework/EC_Operational_Framework/Model_Repository/lib/LWCB_WATFLOOD_DATA.sqlite"
#Range=""
#DBSource="Z:/LWS_Db/lwcb.mdb"

# locationquerySQL<-function(StationNumber,DBSource,SQL=FALSE){
#   #Function to query the DailyMaster table to find the latitude, longitude and elevation of a station
#   
#   #Connect to Database
#   if(SQL==TRUE){
#   drv <-dbDriver("SQLite")
#   LWDB<-dbConnect(drv,DBSource)
#   }
#   
#   Location<-dbGetQuery(LWDB,paste("SELECT DailyMaster.StationNumber, Locations.Longitude, Locations.Latitude, Locations.Elevation, Locations.Drainage_Area
#                      FROM DailyMaster INNER JOIN Locations ON DailyMaster.Location = Locations.LocationID
#                      WHERE (((DailyMaster.StationNumber)=",StationNumber,"))",sep=""))
#   dbDisconnect(LWDB)
#   Location<-as.numeric(Location)
#   names(Location)<-c("Station","Longitude","Latitude","Elevation","Drainage_Area")
#   return(Location)
# }
