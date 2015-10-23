# libWATFLOOD.R
#
# library for processing standard watflood file types

source("rlib/libHydroStats.R")

month.str <- c("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


ReadEVT <- function(file.name){
  
  lines <- readLines(file.name)
  lines.count <- length(lines)
  
  no.events.line <- grep(pattern = "noeventstofollow", ignore.case=T, lines)
  eof.line <- grep(pattern = "eof", ignore.case=T, lines)
  
  #set keywords
  header.lines <- lines[1:no.events.line]
  keywords <- ParseHeaderLines(header.lines)
  
  #extract event lines
  event.lines <- lines[(no.events.line+1):(eof.line-1)]
  event.lines <- Trim(event.lines)
  #remove comments
  event.lines <- event.lines[!grepl(pattern="^#", event.lines)]
  
  out.list <- list(keywords=keywords, events.to.follow=event.lines)
  
  return(out.list)
  
}


ReadSplCsv <- function(file.name, stations, start.date="1900-01-01"){
    
  spl <- read.csv(file.name, header=T)
  
  spl[spl<0] = NA
  start.date <- as.Date(start.date)
  spl.date <- start.date + (spl[,1]/24 -1)
  
  spl <- spl[,2:dim(spl)[2]]
  
  
  #Split the data into two separate tables - one for observed, the other for estimated
  
  obs.cols <- seq(1,dim(spl)[2],2)
  est.cols <- seq(2,dim(spl)[2],2)
  
  spl.obs <- spl[,obs.cols]
  spl.est <- spl[,est.cols]
    
  colnames(spl.obs) <- c(stations)
  colnames(spl.est) <- c(stations)
  
  out.list <- list(observed.table=spl.obs, estimated.table=spl.est, stations=stations, date.time=spl.date)
    
}

ReadSplCsvWheader <- function(file.name){
  
  spl <- read.csv(file.name, header=T,check.names=F)
  
  spl[spl==(-1)] = NA
  
  #get start date from header
  start.date <- as.Date(colnames(spl)[1])
  spl.date <- start.date + (spl[,1]/24 -1)
  
  #remove time from first column
  spl <- spl[,2:dim(spl)[2]]
  

  
  #Split the data into two separate tables - one for observed, the other for estimated
  
  obs.cols <- seq(1,dim(spl)[2],2)
  est.cols <- seq(2,dim(spl)[2],2)
  
  spl.obs <- spl[,obs.cols]
  spl.est <- spl[,est.cols]
  
  #Remove extraneous characters from column names
  StationNames<-gsub(" ","",gsub("_","",gsub("obs","",colnames(spl.obs))))
  
  colnames(spl.obs) <- StationNames
  colnames(spl.est) <- StationNames
  
  out.list <- list(observed.table=spl.obs, estimated.table=spl.est, stations=StationNames, date.time=spl.date)
  
}

SplStatsTable <- function(spl, station.list=NA, exclude.na=F, xts.period="/"){
  #generate a table of statistics for the streamflow results from spl.csv  
  #spl = spl object parsed using ReadSplCsv
  
  if (is.na(station.list)){
    station.list <- spl$stations      
  }
  
  station.index <- match(station.list, spl$stations)
  
  
  for(i in 1:length(station.index)){
        
    station.name <- spl$stations[station.index[i]]
    print(station.name)
    ts.obs <- xts(spl$observed.table[[station.name]], spl$date.time)
    ts.est <- xts(spl$estimated.table[[station.name]], spl$date.time)
    
    #subset data to specified period
    ts.obs<- ts.obs[xts.period]
    ts.est<- ts.est[xts.period]
    
    nash<-NASH(ts.obs, ts.est, exclude.na=exclude.na)    
    dv <- FlowAnnBias(ts.obs, ts.est, exclude.na=exclude.na)    
    dv_month <- FlowMonthBias(ts.obs, ts.est, exclude.na=exclude.na)    
    mae <- MAE(ts.obs, ts.est, exclude.na=exclude.na)
    mare <- MARE(ts.obs, ts.est, exclude.na=exclude.na)
    na.count <- sum(is.na(ts.obs))
    record.length <- length(ts.obs)
    
    stats <- c(nash, dv, mae, mare, dv_month, na.count, record.length)
    
    if (i==1){
      stats.table <- stats
    } else {
      stats.table <- rbind(stats.table, stats)    
    }  
    
  }
  
  # Add row and column headings
  
  st <- stats.table
  
  rownames(st) <- spl$stations[station.index]
  colnames(st) <- c("nash", "dv", "mae", "mare", paste("dv-", seq(1,12), sep=""), "na.count", "record.length")
  
  return(st)
  
}


SplCsvPlotSheet <- function(spl, png.title, plot.list=NA, xts.period="/", plot.dim=c(3, 4), average.period=NA,ylimit=NA,h=1200,w=1600){
  #RvMbPlot
  
  # Plots the mass balance timeseries on a number of plot sheets
  
  #file.name <- spl.file.name
  png.filename <- png.title
  #spl <- ReadSplCsv(file.name, stations, start.date=start.date)
  spl.obs <- spl$observed.table
  spl.est <- spl$estimated.table
  spl.date.time <- spl$date.time
  stations <- spl$stations
  
  if(!is.na(plot.list)){
    #reduce the station plot list to only include those included in plot.list
    #plot.list <- c("Date", plot.list)
    
    spl.obs <- spl.obs[, plot.list]
    spl.est <- spl.est[, plot.list]    
    
    stations <- plot.list
    
  }
  
  col.count <- dim(spl.est)[2]
  
  #set number of plots per sheet (3x4)
  pps <- plot.dim[1]*plot.dim[2]
  
  #number of plot sheets
  plot.count <- ceiling((col.count-1)/pps) 
  
  for(p in 1:plot.count){
    
    temp.filename<- paste(png.filename, ".", p, ".png", sep="")
    
    png(temp.filename, width=w, height=h, pointsize=25)
    par( mfrow = plot.dim )
    
    start.index <- (p-1)*pps+1
    end.index <- min(start.index+pps-1, col.count)
    
    
    for (i in start.index:end.index){
      
      title<- colnames(spl.obs)[i]    
      ts.obs <- xts(spl.obs[,i], spl.date.time)    
      ts.est <- xts(spl.est[,i], spl.date.time)
      
      #Filter if a filter is specified
      
      ts.obs <- ts.obs[xts.period]
      ts.est <- ts.est[xts.period]
      
      if(!is.na(average.period)){
        
        if(tolower(average.period)=="monthly"){
          ts.obs<- apply.monthly(ts.obs, mean)
          ts.est<- apply.monthly(ts.est, mean)
        
        } else if(tolower(average.period)=="daily"){
          ts.obs<- apply.daily(ts.obs, mean)
          ts.est<- apply.daily(ts.est, mean)
        
        } else if(tolower(average.period)=="yearly"){
          ts.obs<- apply.yearly(ts.obs, mean)
          ts.est<- apply.yearly(ts.est, mean)          
        
        }
        
        
      }
      
      y.lim <- c(0,max(ts.obs,ts.est,ylimit[i], na.rm=T))          
      
      plot(ts.obs,main=title, ylim=y.lim,ylab="Inflow (m3/s)",pch=4)
      lines(ts.obs, col="black",lty=1,lwd=2)
      lines(ts.est, col="red",lty=2,lwd=3,lend=0)
      legend("topleft",title="",legend=c("Observed","Modelled"),col=c("black","red"),lty=c(1,2),lwd=c(3,3))
      
    }
    
    dev.off()
    
  }
  
}

SplDvPlotSheet <- function(spl, png.title, plot.list=NA, xts.period="/", plot.dim=c(3, 4), exclude.na=F){
  
  
  png.filename <- png.title  
  stations <- spl$stations
  dv.columns <- c(5:16)
  
  if(!is.na(plot.list)){
    stations <- plot.list    
  }
  
  #get stats table
  data.table <- SplStatsTable(spl, station.list=stations, exclude.na=exclude.na, xts.period=xts.period)  
  dv.table<- data.table[,dv.columns]
  
  #set number of plots per sheet (3x4 is default)
  pps <- plot.dim[1]*plot.dim[2]
  
  #number of plot sheets
  plot.count <- ceiling((length(stations)-1)/pps) 
  
  
  for(p in 1:plot.count){
    
    temp.filename<- paste(png.filename, ".", p, ".png", sep="")
    
    png(temp.filename, width=1600, height=1200, pointsize=16)
    par( mfrow = plot.dim )
    
    start.index <- (p-1)*pps+1
    end.index <- min(start.index+pps-1, length(stations))
    
    for (i in start.index:end.index){
      
      title<-rownames(dv.table)[i]   
      barplot(dv.table[i,], names.arg=month.str, ylim=c(-1,1), main=title, las=3)
      grid()
    }
    
    dev.off()  
  }
  
  
}