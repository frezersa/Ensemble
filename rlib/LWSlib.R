
#check and install packages if required
list.of.packages <- c("xts","RODBC","scales","gdata","RSQLite","tools","reshape2","stringi")
new.packages <- list.of.packages[!(list.of.packages %in% installed.packages()[,"Package"])]
if(length(new.packages)) install.packages(new.packages,repos='http://cran.us.r-project.org')

#Set of functions created specifically for LWCB
suppressWarnings(suppressMessages(library(xts)))
suppressWarnings(suppressMessages(library(RODBC)))
suppressWarnings(suppressMessages(library(scales)))
suppressWarnings(suppressMessages(library(gdata)))
suppressWarnings(suppressMessages(library(RSQLite)))
suppressWarnings(suppressMessages(library(tools)))
suppressWarnings(suppressMessages(library(stringi)))
suppressWarnings(suppressMessages(library(reshape2)))
Sys.setenv(TZ="GMT") #set time zone (not sure if this is required)



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
  
  #Pad timeseries with NAs
  filled.DataAll.ts<-merge(DataAll.ts,empty,all=TRUE)
  
return(filled.DataAll.ts)
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
  
  #if column spacing isn't provided, calculate find the maximum space for each column
  #in the dataframe
  if(is.na(colspace[1])){
    if(nrow(df)>1){ #if the dataframe has multiple rows
      nn <- apply(df,2,nchar)
      n <- as.matrix(apply(nn,2,max))
    }else{ #else if the dataframe has a single row
      n <- nchar(df)
    }
  }else{
  n <- colspace
  } 
  
  fmts <- paste0("%-",n, "s") #format code '-' means align left
  
  column_names <- vector()
  d <- apply(df, 2, format) #convert to a matrix of characters
  
  if(nrow(df)>1){ #if the dataframe has multiple rows
    for(i in 1:length(cnames)){
      column_names[i] <- sprintf(fmts[i], cnames[i])
      d[,i] <- sprintf(fmts[i], trim(d[,i]))
    }
      
  }else{ #else the dataframe has a single row
    column_names <- sprintf(fmts,cnames)
    d <- sprintf(fmts,trim(d))
    d <- t(d) 
  }
    
  #write to file unless toggle is turned on
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

