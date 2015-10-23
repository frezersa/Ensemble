#**************************************
#Script to plot spl.csv output for LWCB flow stations. 
#**************************************

rm(list=ls())
cat("Generating SPL Plots \n")

# args provided by rscript
args <- commandArgs(TRUE)
# script directory
cat(script_directory <- args[1])
cat("\n")
# script_directory <-"C:/Test_Framework/EC_Operational_Framework/Model_Repository/scripts"

cat(write_graphics_directory <- args[2])
cat("\n")
# write_graphics_directory <- "C:/Test_Framework/EC_Operational_Framework/Model_Repository/diagnostic"

# output from model run spl.csv
cat(file.spl <- args[3])
cat("\n")
# file.spl <-"C:/Test_Framework/EC_Operational_Framework/Model_Repository/wpegr/results/spl.csv"

#optional start and end dates
cat(start_date<-args[4])
cat("\n")
#start_date<-"2015-01-01"

cat(end_date<-args[5])
cat("\n")
# end_date<-" "
if(length(end_date)<10)end_date<-NA

cat(use_spinup<-args[6])
cat("\n\n")
# use_spinup<-"TRUE"
# if(is.na(use_spinup)) use_spinup<-FALSE

# set working directory to where script is called from. necessary libs will be relative to that
setwd(script_directory)

# libraries to import
source("rlib/libWATFLOOD_IO.R")
source("rlib/libENSIM_IO.R")
library(xts)


# Load spl csv file
spl <- ReadSplCsvWheader(file.spl)

plot.dim <- c(3,3)
exclude.na=T

start_year<-format(spl[[4]][1],"%Y")

if(use_spinup!="False"){
  spl_spin <-ReadSplCsvWheader(use_spinup)
  for(i in 1:2) spl[[i]]<-rbind(spl_spin[[i]],spl[[i]])
  spl[[4]]<-c(spl_spin[[4]],spl[[4]])
}

if(!is.na(start_date)&!is.na(end_date)){
  xts.period<-paste0(start_date,"/",end_date)}else if(
    !is.na(start_date)){xts.period<-paste0(start_date,"/")}else if(
      !is.na(end_date)){xts.period<-paste0("/",end_date)}else{xts.period<-"/"}

SplCsvPlotSheet(spl, paste(write_graphics_directory,"/","spl_daily_",start_year,sep=""), xts.period=xts.period, average.period="daily", plot.dim=plot.dim)

