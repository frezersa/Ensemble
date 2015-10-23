#script to create YYYMMDD_dif.r2c files
# the file is the gridded daily variation in temperature and calculated from hourly gridded temperature files
#in our case there is a grid every 3 hours
#ultimately this is something that should be done in tmp64x.exe, but it currently only calculates it when a temp.tb0 file is provided,
#this won't work for use because I'm using gridded temperature files from the GEM model (received in August 2015 from Bruce Davidson)
rm(list=ls())
#Set of functions created specifically for LWCB
#check and install packages if required
list.of.packages <- c("xts","RODBC","scales","gdata","RSQLite","tools","reshape2","raster","rts")
new.packages <- list.of.packages[!(list.of.packages %in% installed.packages()[,"Package"])]
if(length(new.packages)) install.packages(new.packages,repos='http://cran.us.r-project.org')

suppressWarnings(suppressMessages(library(xts)))
suppressWarnings(suppressMessages(library(RODBC)))
suppressWarnings(suppressMessages(library(scales)))
suppressWarnings(suppressMessages(library(gdata)))
suppressWarnings(suppressMessages(library(RSQLite)))
suppressWarnings(suppressMessages(library(tools)))
suppressWarnings(suppressMessages(library(reshape2)))
suppressWarnings(suppressMessages(library(raster)))
suppressWarnings(suppressMessages(library(rts)))
Sys.setenv(TZ="GMT") #set time zone (not sure if this is required)

#get arguments
args <- commandArgs(TRUE)
cat(paste("1 - ",script_dir <- args[1]),"\n") #working directory
#cat("this works")

#script_dir <- "C:/WR_WTFLD_Framework_D/Model_Repository/scripts"


tempr_dir <- paste0(script_dir,"/../wpegr/tempr/")
tempr_files <- list.files(tempr_dir)
tem_files <- tempr_files[grep("tem",tempr_files)]


stackr2c <- function(r2cfile){
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
    tmpframe<-matrix(as.numeric(unlist(strsplit(jam," +"))),frame.length,byrow=T)*1 #(convert to mm)
    
    #Convert to a raster
    r <- raster(nrow=nrow(tmpframe), ncol=ncol(tmpframe),xmn=xmn,xmx=xmx,ymn=ymn,ymx=ymx)
    names(r)<-unlist(strsplit(FrameData,"\""))[2]
    r[] <- tmpframe
    
    return(r)
  })
  )
  
  output<-list(header.lines,rr)
  return(output)
}

#function to write r2c file
writer2c<-function(header,data,FileName="default.r2c"){
  
  #Write header to the file
  writeLines(header, con = FileName)
  
  
  writeBrick<-function(i){
    
    timestamp<-as.POSIXct(strptime(names(data[[i]]),"X%Y.%m.%d"),tz="GMT")
    frameheader<-paste0(":Frame  ",i,"   ",i,"   \"",format(timestamp,"%Y/%m/%d %H:%M"),"\"")
    framedata<-apply(as.matrix(data[[i]]),2,function(x) sprintf("%.1f",x,quote=F))
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
#for(i in tem_files){print()}
for(i in tem_files){
  Year <- substr(i,1,4)
  outname <- gsub("tem","dif",i)
  
  #Plot single year***********************************
  lines<-readLines(paste0(tempr_dir,i))

  r2cfile<-lines
  #create raster brick
  timestack<-stackr2c(lines)

  #timestack[[2]]<-flip(timestack[[2]],'y') #the frame orgin of y-axis is opposite in r2c and raster templates
  
  # create timeseries
  timestamps<-as.POSIXct(strptime(names(timestack[[2]]),"X%Y.%m.%d.%H.%M"))
  timestack.xts<-rts(timestack[[2]],timestamps)

  #timestack.xts
  #plot(timestack.xts,"20040101")
  
  #get max and min for each day
  timestack.min <- apply.daily(timestack.xts,min)
  timestack.max <- apply.daily(timestack.xts,max)
  days <- as.Date(index(timestack.max))


  
  
  timestack.diff <- do.call("stack",lapply(c(1:length(index(timestack.min))),
                           function(i){
                             diff <- timestack.max[[i]] - timestack.min[[i]]
                           }))

  names(timestack.diff) <- days

  
  
  writer2c(timestack[[1]],timestack.diff,FileName=paste0(tempr_dir,outname))

}