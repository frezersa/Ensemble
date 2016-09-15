#**************************************
#Script to process Ensemble Data
#Calculates percentiles of the forecast data and then outputs results
#to plots and csvs.Also requires hindcast data because outputs have a 2-week lookback period
#****************************************

rm(list=ls())

#check and install packages if required
list.of.packages <- c("ggplot2")
new.packages <- list.of.packages[!(list.of.packages %in% installed.packages()[,"Package"])]
if(length(new.packages)) install.packages(new.packages,repos='http://cran.us.r-project.org')

#Get arguments
args <- commandArgs(TRUE)
cat(paste("1 - ",script_directory <- args[1]),"\n") #working directory
# script_directory <- "Q:/WR_Ensemble_dev/A_MS/Repo/scripts"

cat(paste("1 - ",model_directory <- args[2]),"\n") #typically 'wpegr'
# model_directory <- "wpegr"

cat(paste("3 - ",Forecast <- args[3]),"\n") #typically 'wpegr'
# Forecast <- "False"

#set working directory and load libraries
setwd(script_directory)
source("rlib/libWATFLOOD_IO.R")
source("rlib/libENSIM_IO.R")
source("rlib/LWSlib.R")

#set directory paths
forecast_directory <- file.path(dirname(script_directory),"forecast")
output_directory <- file.path(dirname(script_directory),"diagnostic")
if(Forecast == "True" || Forecast == "TRUE" || Forecast == TRUE){
  hindcast_directory <- file.path(dirname(dirname(script_directory)),"Repo_hindcast")
}else{
  hindcast_directory <- dirname(script_directory)
}








#define plotting function
inflowplots <- function(percentileframe,resin_hind,LakeName,m,avg=FALSE){
  
  #if there is no forecast data
  if(percentileframe == FALSE){
    tdf<-merge(Obs=zoo(resin_hind$observed.table[,m],resin_hind$date.time),Est=zoo(resin_hind$estimated.table[,m],resin_hind$date.time))
  }else{ #else plot the forecast data also
    #create data frame for ggplot to work with
    futuredates<-tail(resin_hind$date.time,n=1) + c(1:10)
    tdf<-merge(Obs=zoo(resin_hind$observed.table[,m],resin_hind$date.time),Est=zoo(resin_hind$estimated.table[,m],resin_hind$date.time),
               Min=zoo(percentileframe[c(2),],futuredates),Max=zoo(percentileframe[c(6),],futuredates),Med=zoo(percentileframe[c(4),],futuredates))
  }
  
  #subset
  #tdf<-window(tdf,start=as.Date("2014-08-15"))
  
  #create 7 day moving average
  if(avg){
    if(percentileframe != FALSE){
      tdf[tail(resin_hind$date.time[],7),3:5] <- tdf[tail(resin_hind$date.time[],7),2] #append observed so that average can be applied to forecast
    }
    tdf <- round(rollapply(tdf,FUN=mean,width=7,align="right"),1)
  }
  
  #plot
  #if there is no forecast data
  if(percentileframe == FALSE){
    p   <-  ggplot(data=fortify(tdf),aes(x=Index)) +
      geom_line(aes(y = Obs,col="black"),size=0.5) +
      geom_line(aes(y=Est,col="red"),size=0.5) +
      theme_bw() + xlab("Date") + ylab("Flow (m3/s)") + ggtitle(LakeName) +
      scale_y_continuous(limits=c(min(0,tdf$Obs,na.rm=T),max(tdf$Obs,na.rm=T))) +
      scale_colour_manual(name = '', 
                          values =c('black'='black','red'='red'), labels = c('Observed','Modelled \n (Median)')) +
      theme(legend.position=c(0.3,.9),legend.box='horizontal',legend.direction='horizontal',
            legend.text = element_text(size=5), legend.key.size = unit(0.5, "cm"))
    
  }else{
    p   <-  ggplot(data=fortify(tdf),aes(x=Index)) +
      geom_line(aes(y = Obs,col="black"),size=0.5) +
      geom_line(aes(y=Est,col="red"),size=0.5) +
      geom_ribbon(aes(ymin=Min,ymax=Max,fill="dimgray"),alpha=.4) +
      geom_line(aes(y=Med),size=0.5,col="red") +
      theme_bw() + xlab("Date") + ylab("Flow (m3/s)") + ggtitle(LakeName) +
      scale_y_continuous(limits=c(min(0,tdf$Obs,na.rm=T),max(tdf$Obs,na.rm=T))) +
      scale_fill_identity(name = '', guide = 'legend',labels = c('90% Conf.')) +
      scale_colour_manual(name = '', 
                          values =c('black'='black','red'='red'), labels = c('Observed','Modelled \n (Median)')) +
      theme(legend.position=c(0.3,.9),legend.box='horizontal',legend.direction='horizontal',
            legend.text = element_text(size=5), legend.key.size = unit(0.5, "cm"))
  }
  return(p) 
}




#main part of script**************************************


#get hindcast
file.resin_hindcast<-file.path(hindcast_directory,model_directory,"results", "spl.csv")
resin_hind <-ReadSplCsvWheader(file.resin_hindcast)

#get number of reservoirs in results
num_reservoirs <- length(resin_hind$stations)

#get the files names
file_names <- list.files(path=forecast_directory,pattern = "spl" )

#if there are forecast files, then get and plot the forecast
if(Forecast == "True" || Forecast == "TRUE" || Forecast == TRUE){
  #Initialize list
  emptyframe <- data.frame()
  MasterList <- replicate(num_reservoirs,emptyframe,)
  
  #loop through to sort all values by reservoir
  for(i in file_names){
    file.resin <- file.path(forecast_directory,i)
    resin <- ReadSplCsvWheader(file.resin)
    
    for(j in 1:num_reservoirs){
      MasterList[[j]]<-rbind(MasterList[[j]],resin$estimated.table[,j])
    }
  }
  
  #Calculate percentiles from reservoir estimates
  probs=c(0,.05,.25,.5,.75,.95,1)
  MasterPerc<-list()
  for(k in 1:length(MasterList)){
    MasterPerc[[k]]<-apply(MasterList[[k]],2,quantile,probs=probs)
  }
}



LakeNames<- resin_hind$stations




output<-data.frame()
#loop to plot
for(m in 1:num_reservoirs){
  
  if(Forecast == "True" || Forecast == "TRUE" || Forecast == TRUE){
    assign(paste0("p",m),inflowplots(percentileframe=MasterPerc[[m]],resin_hind=resin_hind,LakeName=LakeNames[m],m=m))


  }else{ #else there is a forecast
    assign(paste0("p",m),inflowplots(percentileframe=FALSE,resin_hind=resin_hind,LakeName=LakeNames[m],m=m))
  }

}


#Export plots
png(file.path(output_directory,"Streamflows_1.png"),res=150,width=2000,height=1300)
suppressWarnings(multiplot(p1,p2,p3,p4,p5,p6,p7,p8,p9,cols=3))
garbage<-dev.off()

png(file.path(output_directory,"Streamflows_2.png"),res=150,width=2000,height=1300)
suppressWarnings(multiplot(p10,p11,p12,p13,p14,p15,p16,p17,p18,cols=3))
garbage<-dev.off()

png(file.path(output_directory,"Streamflows_3.png"),res=150,width=2000,height=1300)
suppressWarnings(multiplot(p19,p20,p21,p22,p23,p24,p25,p26,p27,cols=3))
garbage<-dev.off()



