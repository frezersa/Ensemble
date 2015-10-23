#**************************************
#Script to plot resin.csv output for LWCB Reservoir Inflow. 
#**************************************


rm(list=ls())

cat("Generating Resin Plots \n")

# args provided by rscript
args <- commandArgs(TRUE)
# script directory
cat(script_directory <- args[1])
# script_directory <-"C:/Test_Framework/EC_Operational_Framework/Model_Repository/scripts"
cat("\n")
cat(write_graphics_directory <- args[2])
cat("\n")
# write_graphics_directory <- "C:/Test_Framework/EC_Operational_Framework/Model_Repository/diagnostic"

# output from model run resin.csv
cat(file.resin <- args[3])
cat("\n")
# file.resin <-"C:/Test_Framework/EC_Operational_Framework/Model_Repository/wpegr/results/resin.csv"

#optional start and end dates
cat(start_date<-args[4])
cat("\n")
# start_date<-"2014-01-01"

cat(end_date<-args[5])
cat("\n")
# end_date<-NA
if(length(end_date)<10)end_date<-NA

cat(use_spinup<-args[6])
cat("\n\n")
# use_spinup<-"C:/Ensemble_Framework/EC_Operational_Framework/Model_Repository_hindcast_adjusted/wpegr/results/resin.csv"
if(is.na(use_spinup)) use_spinup<-FALSE

# set working directory to where script is called from. necessary libs will be relative to that
setwd(script_directory)

# libraries to import
source("rlib/libWATFLOOD_IO.R")
source("rlib/libENSIM_IO.R")

# Load resin file
plot.dim <- c(2,2)

resin <- ReadSplCsvWheader(file.resin)
start_year<-format(resin[[4]][1],"%Y")


if(use_spinup!="False"&use_spinup!=FALSE){
  file.resin_spinup<-use_spinup
  resin_spin <-ReadSplCsvWheader(file.resin_spinup)
  for(i in 1:2) resin[[i]]<-rbind(resin_spin[[i]],resin[[i]])
  resin[[4]]<-c(resin_spin[[4]],resin[[4]])
}

if(!is.na(start_date)&!is.na(end_date)){
  xts.period<-paste0(start_date,"/",end_date)}else if(
    !is.na(start_date)){xts.period<-paste0(start_date,"/")}else if(
      !is.na(end_date)){xts.period<-paste0("/",end_date)}else{xts.period<-"/"}

#reorder reservoirs
for(i in 1:2) resin[[i]]<-resin[[i]][,c(4,5,6,1,3,2,7)]
resin[[3]]<-resin[[3]][c(4,5,6,1,3,2,7)]
colnames(resin$observed.table)<-c("Lac La Croix","Namakan Lake","Rainy Lake","Lake of the Woods","Lake St. Joseph","Lac Seul","Caribou Falls Reservoir")

SplCsvPlotSheet(resin, paste(write_graphics_directory,"/","resin_1DayAvg_",start_year,sep=""), xts.period=xts.period, plot.dim=plot.dim, average.period="daily")

#Export combined resin csv
output<-cbind(resin$observed,resin$estimated)
output<-output[,c(1,8,2,9,3,10,4,11,5,12,6,13,7,14)]
row.names<-resin$date.time
write.csv(output,paste0(write_graphics_directory,"/resin_1day.csv"))

#run 7-day average on the estimated inflows (observed is also 7-day average)
estimated.xts<-xts(resin$estimated.table,resin$date.time)
if(nrow(estimated.xts)>7){estimated.xts<-round(rollapply(estimated.xts,FUN=mean,width=7))}
resin$estimated.table<-as.data.frame(estimated.xts)

observed.xts<-xts(resin$observed.table,resin$date.time)
if(nrow(observed.xts)>7){observed.xts<-round(rollapply(observed.xts,FUN=mean,width=7))}
resin$observed.table<-as.data.frame(observed.xts)

SplCsvPlotSheet(resin, paste(write_graphics_directory,"/","resin_7DayAvg_",start_year,sep=""), xts.period=xts.period, plot.dim=plot.dim, average.period="daily")

#Export combined resin csv
output<-cbind(resin$observed,resin$estimated)
output<-output[,c(1,8,2,9,3,10,4,11,5,12,6,13,7,14)]
write.csv(output,paste0(write_graphics_directory,"/resin_7day.csv"))
row.names<-resin$date.time