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
# script_directory <- "Q:/WR_Ensemble_dev/A_MS/Repo/scripts"

cat(paste("2 - ",parentfolder <- args[2]),"\n") 
# parentfolder <- "Q:/WR_Ensemble_dev/A_MS/Repo/diagnostic"

cat(paste("3 - ",met_forecast_file <- args[3]),"\n") 
# met_forecast_file <- "Q:/WR_Ensemble_dev/A_MS/Repo/wpegr/radcl/20160914_met_03-01.r2c"

cat(paste("4 - ",tem_forecast_file <- args[4]),"\n") 
# tem_forecast_file <- "Q:/WR_Ensemble_dev/A_MS/Repo/wpegr/tempr/20160914_tem_03-01.r2c"

cat(paste("5 - ",met_hindcast_file <- args[5]),"\n") 
# met_hindcast_file <- "Q:/WR_Ensemble_dev/A_MS/Repo_hindcast/wpegr/radcl/20160101_met.r2c"

cat(paste("6 - ",forecast_date <- as.Date(args[6])),"\n") 
# forecast_date <- as.Date("2016-09-14")


#set some defaults
shapefile_directory <- file.path(dirname(script_directory),"lib","shapefiles")
source(file.path(script_directory,"rlib", "LWSlib.R"))

#get shapefiles boundaries
boundary <- readOGR(dsn=shapefile_directory,layer="Watershed",verbose=F)
provinces <-readOGR(dsn=shapefile_directory,layer="ne_10m_admin_1_states_provinces_lakes_shp",verbose=F)
lakes <-readOGR(dsn=shapefile_directory,layer="ne_10m_lakes",verbose=F)
rivers <- readOGR(dsn=shapefile_directory,layer="ne_10m_rivers_lake_centerlines",verbose=F)

# get forecast
lines <- readLines(met_forecast_file)

#create raster brick
timestack <- stackr2c(lines)
timestack <- flip(timestack,'y') #the frame orgin of y-axis is opposite in r2c and raster templates

#get date and time information from raster brick
#separate by days to plot each day
timestamps <- names(timestack)
timestamps <- as.POSIXct(strptime(timestamps,"X%Y.%m.%d.%H.%M"))
if(is.na(timestamps[1]))cat("Error-the time format does not match that in the r2c file, please correct in the script forecastmaps.R (approx. line 57)")
timestamps[length(timestamps)] <- timestamps[length(timestamps)]-1 #last raster is moved up one day
datestamps <- as.Date(timestamps,tz="GMT")
uniquedates <- unique(datestamps)





#Plot Daily precip forecast**********************************


#create raster stack consisting of each day (similar to what we do for temp)
timestack.day <- do.call("stack",lapply(1:length(uniquedates),function(k){
  tmpvec <- c(1:length(datestamps))[datestamps==uniquedates[k]]
  tmpframe <- sum(subset(timestack,tmpvec))
  return(tmpframe)
  }
  ))


#plot daily precip forecast
myTheme=rasterTheme(region=(brewer.pal(9, 'Blues')))
names(timestack.day) <- format(uniquedates, format="%b %d")
p <- levelplot(timestack.day,margin=F,par.settings=myTheme,contour=T,labels=F,
              alpha.regions=.7,
              main="Daily Precip Forecast (mm)",
              at=seq(0,100,10)) +
  layer(sp.polygons(boundary,lwd=2,col='darkgray')) +
  layer(sp.polygons(provinces,lwd=1,col='black'))



#Save plot
png(file.path(parentfolder,"Met_Forecast_DailyPrecip.png"),
    width=20,height=16,units="cm",res=90)
p
garbage<-dev.off()
cat("Met_Forecast_DailyPrecip.png\n")





#Plot weekly precip forecast*********************************************

#define the dates we want
next_week <- forecast_date + 7
frames_to_get <- seq(1,length(timestamps),1)[timestamps<as.POSIXct(next_week)]
total.precip <- sum(subset(timestack,frames_to_get))




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
png(file.path(parentfolder,"Met_Forecast_Precip7Days.png"),
    width=20,height=16,units="cm",res=90)
p
garbage<-dev.off()
cat("Met_Forecast_Precip7Days.png\n")









#Plot hindcast***********************************
lines<-readLines(met_hindcast_file)

#create raster brick
timestack<-stackr2c(lines)
timestack<-flip(timestack,'y') #the frame orgin of y-axis is opposite in r2c and raster templates


#get date and time information from raster brick
#separate by days to plot each day
timestamps <- names(timestack)
timestamps <- as.POSIXct(strptime(timestamps,"X%Y.%m.%d.%H.%M"))
if(is.na(timestamps[1]))cat("Error-the time format does not match that in the r2c file, please correct in the script forecastmaps.R (approx. line 57)")
timestamps[length(timestamps)] <- timestamps[length(timestamps)]-1 #last raster is moved up one day
datestamps <- as.Date(timestamps,tz="GMT")
uniquedates <- unique(datestamps)


plot_hindcast <- function(timestack, timestamps, forecast_date, days, title){
  #define the dates we want
  early_date <- forecast_date - days
  late_date <- forecast_date
  frames_to_get <- seq(1,length(timestamps),1)[timestamps>as.POSIXct(early_date) & timestamps<=as.POSIXct(late_date)]
  past.precip <- sum(subset(timestack,frames_to_get))
  
  
  #plot the predicted precip
  p <- levelplot(past.precip,margin=F,par.settings=myTheme,contour=T,labels=T,
                 alpha.regions=.7,
                 main=title,
                 at=seq(0, max.precip,20)) +
    layer(sp.polygons(provinces,lwd=1,col='black'),under=T) +
    layer(sp.lines(rivers,lwd=1,col='black'),under=T) +
    layer(sp.polygons(lakes,lwd=1,fill='gray',col='black'),under=T) +
    layer(panel.text(-90.5, 47.5, forecast_date),under=F)
  

  return(p)
}


#Plot last 7 days*********************************************
out_filename <- "Met_Hindcast_Precip7days.png"
png(file.path(parentfolder,out_filename),
    width=20,height=16,units="cm",res=90)
plot_hindcast(timestack, timestamps, forecast_date, 7, "Precipitation (mm) Over Past 7 Days")
garbage <- dev.off()
cat(out_filename,"\n")

#Plot last 1 day*********************************************
out_filename <- "Met_Hindcast_Precip1days.png"
png(file.path(parentfolder,out_filename),
    width=20,height=16,units="cm",res=90)
plot_hindcast(timestack, timestamps, forecast_date, 1, "Precipitation (mm) Over Past 24 Hours")
garbage <- dev.off()
cat(out_filename,"\n")

#Plot last 2 days*********************************************
out_filename <- "Met_Hindcast_Precip2days.png"
png(file.path(parentfolder,out_filename),
    width=20,height=16,units="cm",res=90)
plot_hindcast(timestack, timestamps, forecast_date, 2, "Precipitation (mm) Over Past 48 Hours")
garbage <- dev.off()
cat(out_filename,"\n")

#Plot last 3 days*********************************************
out_filename <- "Met_Hindcast_Precip3days.png"
png(file.path(parentfolder,out_filename),
    width=20,height=16,units="cm",res=90)
plot_hindcast(timestack, timestamps, forecast_date, 3, "Precipitation (mm) Over Past 72 Hours")
garbage <- dev.off()
cat(out_filename,"\n")






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
myTheme=rasterTheme(region=rev(brewer.pal(9, 'RdYlBu')))
names(timestack.day)<-format(uniquedates, format="%b %d")
p <-levelplot(timestack.day,margin=F,par.settings=myTheme,alpha.regions=.7,contour = T,
              main="Forecast Average Temperature (C)",
              at=seq(-30,30,5)) +
  layer(sp.polygons(boundary,lwd=2,col='darkgray')) +
  layer(sp.polygons(provinces,lwd=1,col='black'))


#Save plot
png(file.path(parentfolder,"Met_Forecast_Temp.png"),
          ,width=20,height=16,units="cm",res=90)
p
garbage<-dev.off()
cat("Met_Forecast_Temp.png\n")





#*********************************************************************
#plot rainfall ensembles

#get rainfall files from same directory that deterministic rainfall data was found
met_directory <- dirname(met_forecast_file)
met_ensemble_filenames <- list.files(met_directory)
outputfolder<-file.path(dirname(script_directory),"diagnostic")


i=1
meanprecip<-vector()
for(i in 1:length(met_ensemble_filenames)){

  # get forecast*******
  lines<-readLines(file.path(met_directory,met_ensemble_filenames[i]))
  
  #create raster brick
  timestack<-stackr2c(lines)
  timestack<-flip(timestack,'y') #the frame orgin of y-axis is opposite in r2c and raster templates
  
  #get date and time information from raster brick
  #separate by days to plot each day
  timestamps <- names(timestack)
  timestamps <- as.POSIXct(strptime(timestamps,"X%Y.%m.%d.%H.%M"))
  if(is.na(timestamps[1]))cat("Error-the time format does not match that in the r2c file, please correct in the script forecastmaps.R (approx. line 57)")
  timestamps[length(timestamps)] <- timestamps[length(timestamps)]-1 #last raster is moved up one day

  #define the dates we want
  next_week <- forecast_date + 7
  frames_to_get <- seq(1,length(timestamps),1)[timestamps<as.POSIXct(next_week)]
  total.precip <- sum(subset(timestack,frames_to_get))
  
  
  #calculate the spatial average
  meanprecip[i]<-mean(total.precip@data@values)
  
  #create raster stack consisting of each ensemble spatial average
  if(i==1){timestack.ensemble<-total.precip}else{
    timestack.ensemble<-stack(timestack.ensemble,total.precip)}
}
  
#create index of weekly sums and find the 10th, 25th, 75th and 90th percentiles
#these are ranked according to the spatial average of the total (temporal) forecast precip over the next week
percIndex<-data.frame(Sim=c(1:length(met_ensemble_filenames)),meanprecip)
percIndex <- percIndex[order(meanprecip),]

percentile.key <- round(quantile(percIndex$Sim,c(0.1,0.25,0.75,0.9)))
timestack.percentile<-subset(timestack.ensemble,percentile.key)

#plot daily precip forecast
myTheme=rasterTheme(region=(brewer.pal(9, 'Blues')))
names(timestack.percentile)<-c("P-10th","P-25th","P-75th","P-90th")
names(timestack.percentile)
p <-levelplot(timestack.percentile,margin=F,par.settings=myTheme,contour=T,labels=T,
              alpha.regions=.7, layout=c(2,2),
              main=paste0("7-Day Cumulative Precipitation - Ensemble Forecasts (Ranked by basin mean)"),
              at=seq(0,100,20)) +
  layer(sp.polygons(boundary,lwd=2,col='darkgray')) +
  layer(sp.polygons(provinces,lwd=1,col='black'))


png(file.path(outputfolder,"Met_Forecast_PrecipEns.png"),
    ,width=20,height=16,units="cm",res=90)
print(p)
garbage<-dev.off()
cat("Met_Forecast_PrecipEns.png\n")


