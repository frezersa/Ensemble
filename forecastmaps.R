#****************************************
#script to produce maps of forecast precip (deterministic and ensemble) and temp (deterministic) data,
#and hindcast precip data (CaPA). It uses shapefiles located in the lib directory.
#****************************************
rm(list=ls())
#sink("NUL")

#check and install packages if required
list.of.packages <- c("raster","rasterVis","colorspace","rgdal","lattice","latticeExtra")
new.packages <- list.of.packages[!(list.of.packages %in% installed.packages()[,"Package"])]
if(length(new.packages)) install.packages(new.packages,repos='http://cran.us.r-project.org')

suppressWarnings(suppressMessages(library(raster)))
suppressWarnings(suppressMessages(library(rasterVis)))
suppressWarnings(suppressMessages(library(colorspace)))
suppressWarnings(suppressMessages(library(rgdal)))
suppressWarnings(suppressMessages(library(lattice)))
suppressWarnings(suppressMessages(library(latticeExtra)))
myTheme=rasterTheme(region=rev(sequential_hcl(10, power=2.2)))
Sys.setenv(TZ='GMT')

#Get arguments
args <- commandArgs(TRUE)
cat(paste("1 - ",script_directory <- args[1]),"\n") #working directory
#script_directory<-"C:/Test_Framework/EC_Operational_Framework/Model_Repository/scripts"
cat(paste("2 - ",parentfolder <- args[2]),"\n") 
#parentfolder<-"C:/Test_Framework/EC_Operational_Framework/Model_Repository/diagnostic"
cat(paste("3 - ",met_forecast_file <- args[3]),"\n") 
#met_forecast_file<-"C:/Test_Framework/EC_Operational_Framework/Model_Repository/wpegr/radcl/20141210_met_1-00.r2c"
cat(paste("4 - ",tem_forecast_file <- args[4]),"\n") 
#tem_forecast_file<-"C:/Test_Framework/EC_Operational_Framework/Model_Repository/wpegr/tempr/20141210_tem_1-00.r2c"
cat(paste("5 - ",met_hindcast_file <- args[5]),"\n") 
#met_hindcast_file<-"C:/Test_Framework/EC_Operational_Framework/Model_Repository_hindcast_adjusted/wpegr/radcl/Orig_20140101_met.r2c"
cat(paste("6 - ",forecast_date <- as.Date(args[6])),"\n") 
#met_hindcast_file<-"C:/Test_Framework/EC_Operational_Framework/Model_Repository_hindcast_adjusted/wpegr/radcl/Orig_20140101_met.r2c"



shapefile_directory <-paste0(script_directory,"/../lib/shapefiles")
source(paste0(script_directory,"/rlib/LWSlib.R"))




#get shapefiles boundaries
boundary <- readOGR(dsn=shapefile_directory,layer="Watershed",verbose=F)
provinces <-readOGR(dsn=shapefile_directory,layer="ne_10m_admin_1_states_provinces_lakes_shp",verbose=F)
lakes <-readOGR(dsn=shapefile_directory,layer="ne_10m_lakes",verbose=F)
rivers <- readOGR(dsn=shapefile_directory,layer="ne_10m_rivers_lake_centerlines",verbose=F)



# get forecast***************************************
#todaydate<-format(Sys.Date(),"%Y%m%d")
parentfolder<-paste0(parentfolder,"/")
lines<-readLines(met_forecast_file)

#create raster brick
timestack<-stackr2c(lines)
timestack<-flip(timestack,'y') #the frame orgin of y-axis is opposite in r2c and raster templates

#Plot Daily precip forecast**********************************
#separate by days to plot each day
timestamps<-names(timestack)
timestamps<-as.POSIXct(strptime(timestamps,"X%Y.%m.%d.%H.%M"))
if(is.na(timestamps[1]))cat("Error-the time format does not match that in the r2c file, please correct in the script forecastmaps.R (approx. line 57)")
timestamps[length(timestamps)]<-timestamps[length(timestamps)]-1 #last raster is moved up one day
datestamps<-as.Date(timestamps,tz="GMT")
uniquedates<-unique(datestamps)

#create raster stack consisting of each day (similar to what we do for temp)
timestack.day<-do.call("stack",lapply(1:length(uniquedates),function(k){
  tmpvec<-c(1:length(datestamps))[datestamps==uniquedates[k]]
  tmpframe<-sum(subset(timestack,tmpvec))
  return(tmpframe)
  }
  ))


#plot daily precip forecast
myTheme=rasterTheme(region=(brewer.pal(10, 'Blues')))
names(timestack.day)<-format(uniquedates, format="%b %d")
p <-levelplot(timestack.day,margin=F,par.settings=myTheme,contour=T,labels=F,
              alpha.regions=.7,
              main="Daily Precip Forecast (mm)",
              at=seq(0,100,10)) +
  layer(sp.polygons(boundary,lwd=2,col='darkgray')) +
  #layer(sp.lines(rivers,lwd=1,col='black')) +
  #layer(sp.polygons(lakes,lwd=1,fill='lightblue')) +
  layer(sp.polygons(provinces,lwd=1,col='black'))



#Save plot
png(paste0(parentfolder,"Daily_Precip.png"),
    width=20,height=16,units="cm",res=90)
p
garbage<-dev.off()
cat("Daily_Precip.png\n")


#Plot weekly precip forecast*********************************************
total.precip <- sum(subset(timestack,1:56))



#plot the predicted precip
max.precip<-180
myTheme=rasterTheme(region=(brewer.pal(5, 'Blues')))
p <-levelplot(total.precip,margin=F,par.settings=myTheme,contour=T,labels=T,
              alpha.regions=.7,
               main="Predicted Precipitation (mm) Over Upcoming 7 Days",
              at=seq(0, max.precip,20)) +
    #layer(sp.polygons(boundary,lwd=2,col='darkgray')) +
  layer(sp.polygons(provinces,lwd=1,col='black'),under=T) +
  layer(sp.lines(rivers,lwd=1,col='black'),under=T) +
  layer(sp.polygons(lakes,lwd=1,fill='gray',col='black'),under=T) +
  layer(panel.text(-90.5, 47.5, Sys.Date()),under=F)



#Save plot
png(paste0(parentfolder,"Precip_pred.png"),
    ,width=20,height=16,units="cm",res=90)
p
garbage<-dev.off()
cat("Precip_pred.png\n")



#Plot previous 7 days***********************************
lines<-readLines(met_hindcast_file)

#create raster brick
timestack<-stackr2c(lines)
timestack<-flip(timestack,'y') #the frame orgin of y-axis is opposite in r2c and raster templates

past.precip <- (sum(subset(timestack,(nlayers(timestack)-28):(nlayers(timestack)))))


#plot the predicted precip
p <-levelplot(past.precip,margin=F,par.settings=myTheme,contour=T,labels=T,
              alpha.regions=.7,
              main="Precipitation (mm) Over Past 7 Days",
              at=seq(0, max.precip,20)) +
  #layer(sp.polygons(boundary,lwd=2,col='darkgray')) +
  layer(sp.polygons(provinces,lwd=1,col='black'),under=T) +
  layer(sp.lines(rivers,lwd=1,col='black'),under=T) +
  layer(sp.polygons(lakes,lwd=1,fill='gray',col='black'),under=T) +
  layer(panel.text(-90.5, 47.5, Sys.Date()),under=F)




#Save plot
png(paste0(parentfolder,"Precip_hist.png"),
    ,width=20,height=16,units="cm",res=90)
p
garbage<-dev.off()
cat("Precip_hist.png\n")



past.precip24 <- (sum(subset(timestack,(nlayers(timestack)-4):(nlayers(timestack)))))
past.precip48 <- (sum(subset(timestack,(nlayers(timestack)-8):(nlayers(timestack)))))
past.precip72 <- (sum(subset(timestack,(nlayers(timestack)-12):(nlayers(timestack)))))


#plot the predicted precip
p <-levelplot(past.precip24,margin=F,par.settings=myTheme,contour=T,labels=T,
              alpha.regions=.7,
              main="Precipitation (mm) Over Past 24 hrs",
              at=seq(0, max.precip,10)) +
  #layer(sp.polygons(boundary,lwd=2,col='darkgray')) +
  layer(sp.polygons(provinces,lwd=1,col='black'),under=T) +
  layer(sp.lines(rivers,lwd=1,col='black'),under=T) +
  layer(sp.polygons(lakes,lwd=1,fill='gray',col='black'),under=T) +
  layer(panel.text(-90.5, 47.5, Sys.Date()),under=F)




#Save plot
png(paste0(parentfolder,"Precip_hist1days.png"),
    ,width=20,height=16,units="cm",res=90)
p
garbage<-dev.off()
cat("Daily_hist1day.png\n")

#plot the predicted precip
p <-levelplot(past.precip48,margin=F,par.settings=myTheme,contour=T,labels=T,
              alpha.regions=.7,
              main="Precipitation (mm) Over Past 48 hrs",
              at=seq(0, max.precip,10)) +
  #layer(sp.polygons(boundary,lwd=2,col='darkgray')) +
  layer(sp.polygons(provinces,lwd=1,col='black'),under=T) +
  layer(sp.lines(rivers,lwd=1,col='black'),under=T) +
  layer(sp.polygons(lakes,lwd=1,fill='gray',col='black'),under=T) +
  layer(panel.text(-90.5, 47.5, Sys.Date()),under=F)




#Save plot
png(paste0(parentfolder,"Precip_hist2days.png"),
    ,width=20,height=16,units="cm",res=90)
p
garbage<-dev.off()
cat("Daily_hist2days.png\n")

#plot the predicted precip
p <-levelplot(past.precip72,margin=F,par.settings=myTheme,contour=T,labels=T,
              alpha.regions=.7,
              main="Precipitation (mm) Over Past 72 hrs",
              at=seq(0, max.precip,10)) +
  #layer(sp.polygons(boundary,lwd=2,col='darkgray')) +
  layer(sp.polygons(provinces,lwd=1,col='black'),under=T) +
  layer(sp.lines(rivers,lwd=1,col='black'),under=T) +
  layer(sp.polygons(lakes,lwd=1,fill='gray',col='black'),under=T) +
  layer(panel.text(-90.5, 47.5, Sys.Date()),under=F)




#Save plot
png(paste0(parentfolder,"Precip_hist3days.png"),
    ,width=20,height=16,units="cm",res=90)
p
garbage<-dev.off()
cat("Daily_hist3days.png\n")




#Temp forecast***********************************
lines<-readLines(tem_forecast_file)

#create raster brick
timestack<-stackr2c(lines)
timestack<-flip(timestack,'y') #the frame orgin of y-axis is opposite in r2c and raster templates

timestamps<-names(timestack)
timestamps<-as.POSIXct(strptime(timestamps,"X%Y.%m.%d.%H.%M"))
timestamps[length(timestamps)]<-timestamps[length(timestamps)]-1 #last raster is moved up one day
datestamps<-as.Date(timestamps,tz="GMT")
uniquedates<-unique(datestamps)

timestack.day<-do.call("stack",lapply(1:length(uniquedates),function(k){
  tmpvec<-c(1:length(datestamps))[datestamps==uniquedates[k]]
  tmpframe<-mean(subset(timestack,tmpvec))
  return(tmpframe)
}
))



#plot the predicted temp
myTheme=rasterTheme(region=(brewer.pal(9, 'YlOrRd')))
names(timestack.day)<-format(uniquedates, format="%b %d")
p <-levelplot(timestack.day,margin=F,par.settings=myTheme,alpha.regions=.7,contour = F,
              main="Forecast Average Temperature (C)",
              at=seq(-15, 20,5)) +
  layer(sp.polygons(boundary,lwd=2,col='darkgray')) +
  #layer(sp.lines(rivers,lwd=1,col='black')) +
  #layer(sp.polygons(lakes,lwd=1,fill='lightblue')) +
  layer(sp.polygons(provinces,lwd=1,col='black'))


#Save plot
png(paste0(parentfolder,"Temp_pred.png"),
          ,width=20,height=16,units="cm",res=90)
p
garbage<-dev.off()
cat("Temp_pred.png\n")



#*********************************************************************
#copied from Ensemble forecast Script


i=1
meanprecip<-vector()
for(i in 0:20){

  # get forecast*******
  todaydate<-format(forecast_date,"%Y%m%d")
  parentfolder<-paste0(script_directory,"/../wxData/met/")
  outputfolder<-paste0(script_directory,"/../diagnostic/")
  lines<-readLines(paste0(script_directory,"/../wxData/met/",todaydate,"_met_2-", formatC(i,width=2,format="d",flag="0"), ".r2c"))
  
  #create raster brick
  timestack<-stackr2c(lines)
  timestack<-flip(timestack,'y') #the frame orgin of y-axis is opposite in r2c and raster templates
  
  
  
  #Plot weekly precip forecast*********************************************
  total.precip <- sum(subset(timestack,1:28))
  # total.precip@data@min
  # total.precip@data@max
  meanprecip[i+1]<-mean(total.precip@data@values)
  
  #create raster stack consisting of each day (similar to what we do for temp)
  if(i==0){timestack.ensemble<-total.precip}else{
    timestack.ensemble<-stack(timestack.ensemble,total.precip)}
  
}
  
  percIndex<-data.frame(Sim=c(0:20),meanprecip)
  percIndex <- percIndex[order(meanprecip),]
  percentile.key<-percIndex[c(3,6,15,19),1]+1
  timestack.percentile<-subset(timestack.ensemble,percentile.key)
  
  #plot daily precip forecast
  myTheme=rasterTheme(region=(brewer.pal(10, 'Blues')))
  names(timestack.percentile)<-c("P-10th","P-25th","P-75th","P-90th")
  names(timestack.percentile)
  p <-levelplot(timestack.percentile,margin=F,par.settings=myTheme,contour=T,labels=T,
                alpha.regions=.7, layout=c(2,2),
                main=paste0("7-Day Cumulative Precipitation - Ensemble Forecasts (Ranked by basin mean)"),
                at=seq(0,100,20)) +
    layer(sp.polygons(boundary,lwd=2,col='darkgray')) +
    #layer(sp.lines(rivers,lwd=1,col='black')) +
    #layer(sp.polygons(lakes,lwd=1,fill='lightblue')) +
    layer(sp.polygons(provinces,lwd=1,col='black'))
  
  
  png(paste0(outputfolder,"Precip_Ensemble.png"),
      ,width=20,height=16,units="cm",res=90)
  print(p)
  garbage<-dev.off()
  cat("Precip_Ensemble.png\n")
  

