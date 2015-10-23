# Set Directory to point at R libraries location
main.directory <- "D:/UserData/Alex/UBCWM/Benchmark_Results/Comparison/"
setwd(main.directory)
# Get necessary lib
source("rlib/libENSIM_IO.r")
source("rlib/libHydroStats.R")
source("rlib/libStr.r")
source("rlib/libRAVEN_IO.R")
library(xts)
library(getopt)


Benchmark.Plots <- function(watershed.name,single.year)
{
  #-- 
  # Function to plots the BC Hydro Watersheds Hydrographs from Raven
  # against the results from the UBC-WM
  # Inputs : Watershed_Name (must also be directory name) and Logical
  # Statement to plot a single Year or not
  #--
  
  # Set working directory
  wkdir <- main.directory
  setwd(wkdir)
  
  # Measured data directory
  measured.dir <- "D:/UserData/Alex/UBCWM/UBCWM/Benchmarking/UBCWM.NET/"
  
  # Set the dates to be plotted and get the file names
  if (watershed.name=="ALU")
  {
    directory.name <-"ALU"
    file.name.323 <- paste(wkdir,"R.323/",watershed.name,"/",watershed.name,"_Hydrographs.tb0",sep="")
    date <- "2000-10/2006-09"
    date.1yr <- "2004-10/2005-09"
    file.name.310 <- paste(wkdir,"R.310/",watershed.name,"/",watershed.name,"_Hydrographs.tb0",sep="")
    file.name.measured <- paste(measured.dir,directory.name,"/ModelQ.ts3",sep="")
  } else if (watershed.name=="Campbell") {
    directory.name <-"Campbell"
    file.name.323 <- paste(wkdir,"R.323/",watershed.name,"/",watershed.name,"_Hydrographs.tb0",sep="")
    date <- "1985-10/1990-09"
    date.1yr <-"1986-10/1987-09"
    file.name.310 <- paste(wkdir,"R.310/",watershed.name,"/",watershed.name,"_Hydrographs.tb0",sep="")
    file.name.measured <- paste(measured.dir,directory.name,"/ModelQ.ts3",sep="")
  } else if (watershed.name=="DON") {
    directory.name <-"DON"
    file.name.323 <- paste(wkdir,"R.323/",watershed.name,"/",watershed.name,"_Hydrographs.tb0",sep="")
    date <- "2000-10/2007-09"
    date.1yr <- "2006-10/2007-09"
    file.name.310 <- paste(wkdir,"R.310/",watershed.name,"/",watershed.name,"_Hydrographs.tb0",sep="")
    file.name.measured <- paste(measured.dir,directory.name,"/ModelQ.ts3",sep="")
  } else if (watershed.name=="FIN") {
    directory.name <-"WIF"
    file.name.323 <- paste(wkdir,"R.323/",watershed.name,"/",watershed.name,"_Hydrographs.tb0",sep="")
    date <- "2000-10/2007-09"
    date.1yr <- "2005-10/2006-09"
    file.name.310 <- paste(wkdir,"R.310/",watershed.name,"/",watershed.name,"_Hydrographs.tb0",sep="")
    file.name.measured <- paste(measured.dir,directory.name,"/ModelQ.ts3",sep="")
  } else if (watershed.name=="Illecnew") {
    directory.name <-"Illecnew"
    # Get the output hydrograph from Raven
    file.name.323 <- paste(wkdir,"R.323/",watershed.name,"/",watershed.name,"_Hydrographs.tb0",sep="")
    date <- "1984-10/1989-09"
    date.1yr <- "1986-10/1987-09"
    file.name.310 <- paste(wkdir,"R.310/",watershed.name,"/",watershed.name,"_Hydrographs.tb0",sep="")
    file.name.measured <- paste(measured.dir,directory.name,"/ModelQ.ts3",sep="")
  } else if (watershed.name=="REV2010_100") {
    directory.name <-"Revelstoke"
    # Get the output hydrograph from Raven
    file.name.323 <- paste(wkdir,"R.323/",watershed.name,"/",watershed.name,"_Hydrographs.tb0",sep="")
    date <- "2000-10/2007-09"
    date.1yr <- "2003-10/2004-09"
    file.name.310 <- paste(wkdir,"R.310/",watershed.name,"/",watershed.name,"_Hydrographs.tb0",sep="")
    file.name.measured <- paste(measured.dir,directory.name,"/ModelQ.ts3",sep="")
  }
  
  # Get the output hydrographs from Raven and Measured Data
  if (single.year==TRUE){
    TB0 <- ReadTB0(file.name.323) 
    hydrograph323.ts <- xts(TB0$data.table$Q_1, TB0$data.table$Date)
    hydrograph323.ts <- hydrograph323.ts[date.1yr]
    hydrograph323.ts <- RvTsShift(hydrograph323.ts)
    TB0 <- ReadTB0(file.name.310) 
    hydrograph310.ts <- xts(TB0$data.table$Q_1, TB0$data.table$Date)
    hydrograph310.ts <- hydrograph310.ts[date.1yr]
    hydrograph310.ts <- RvTsShift(hydrograph310.ts)
    ts3 <- ReadTS3(file.name.measured,date.format="%Y/%m/%d %H:%M:%S", is.hydat=F)
    measured.ts<-ts3[3]
    measured.ts <- measured.ts$timeseries
    measured.ts <- measured.ts[date.1yr]
  } else {
    TB0 <- ReadTB0(file.name.323) 
    hydrograph323.ts <- xts(TB0$data.table$Q_1, TB0$data.table$Date)
    hydrograph323.ts <- hydrograph323.ts[date]
    hydrograph323.ts <- RvTsShift(hydrograph323.ts)
    TB0 <- ReadTB0(file.name.310)
    hydrograph310.ts <- xts(TB0$data.table$Q_1, TB0$data.table$Date)
    hydrograph310.ts <- hydrograph310.ts[date]
    hydrograph310.ts <- RvTsShift(hydrograph310.ts)
    ts3 <- ReadTS3(file.name.measured,date.format="%Y/%m/%d %H:%M:%S", is.hydat=F)
    measured.ts<-ts3[3]
    measured.ts <- measured.ts$timeseries
    measured.ts <- measured.ts[date]
  }
  
  # plot
  y.max <- max(hydrograph323.ts,hydrograph310.ts,measured.ts)
  plot(measured.ts, main=paste("Comparison between Observed and Simulated Flows - ", watershed.name), ylab="Flows", ylim=c(0,y.max))
  lines(hydrograph310.ts,col="2")
  lines(hydrograph323.ts,col="4")
  legend("topleft",c("OBSERVED","Raven_R.310","Raven_R.323"),pch=c(20,20,20),col=c(1,2,4),bty="n")
}

# Test the function
Benchmark.Plots("REV2010_100",TRUE)
