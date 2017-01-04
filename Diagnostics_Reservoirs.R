#**************************************
#Script to process Ensemble Data
#Calculates percentiles of the forecast data and then outputs results
#to plots and csvs.Also requires hindcast data because outputs have a 2-week lookback period
#****************************************

rm(list=ls())

#check and install packages if required
list.of.packages <- c("ggplot2","grid")
new.packages <- list.of.packages[!(list.of.packages %in% installed.packages()[,"Package"])]
if(length(new.packages)) install.packages(new.packages,repos='http://cran.us.r-project.org')

#Get arguments
args <- commandArgs(TRUE)
cat(paste("1 - ",script_directory <- args[1]),"\n") #working directory
# script_directory <- "C:/WR/A_MS/Repo/scripts"

cat(paste("1 - ",model_directory <- args[2]),"\n") #need full path
# model_directory <- "C:/WR/A_MS/Repo/wpegr"
model_name <- basename(model_directory)

cat(paste("3 - ",Forecast <- args[3]),"\n") #typically 'wpegr'
# Forecast <- "TRUE"


#set working directory and load libraries
setwd(script_directory)
source("rlib/libWATFLOOD_IO.R")
source("rlib/libENSIM_IO.R")
source("rlib/LWSlib.R")
library(grid)

#set directory paths
forecast_directory <- file.path(dirname(model_directory),"forecast")
output_directory <- file.path(dirname(model_directory),"diagnostic")
if(Forecast == "True" || Forecast == "TRUE" || Forecast == TRUE){
  hindcast_directory <- file.path(dirname(dirname(model_directory)),"Repo_hindcast")
}else{
  hindcast_directory <- dirname(model_directory)
}





#define plotting function
inflowplots <- function(percentileframe,resin_hind,LakeName,m,avg=FALSE){
  
  #if there is no forecast data
  if(percentileframe[[1]] == FALSE){
    tdf<-merge(Obs=zoo(resin_hind$observed.table[,m],resin_hind$date.time),Est=zoo(resin_hind$estimated.table[,m],resin_hind$date.time))
  }else{ #else plot the forecast data also
    #create data frame for ggplot to work with
    futuredates<-tail(resin_hind$date.time,n=1) + c(1:10)
    tdf<-merge(Obs=zoo(resin_hind$observed.table[,m],resin_hind$date.time),
               Est=zoo(resin_hind$estimated.table[,m],resin_hind$date.time),
               Min=zoo(percentileframe[c(2),],futuredates),
               Max=zoo(percentileframe[c(6),],futuredates),
               Med=zoo(percentileframe[c(4),],futuredates),
               lowerq=zoo(percentileframe[c(3),],futuredates),
               upperq=zoo(percentileframe[c(5),],futuredates))
  }
  
  #subset
  #tdf<-window(tdf,start=as.Date("2014-08-15"))
  
  #create 7 day moving average
  if(avg){
    if(percentileframe[[1]] != FALSE){
      tdf[tail(resin_hind$date.time[],7),3:7] <- tdf[tail(resin_hind$date.time[],7),2] #append observed so that average can be applied to forecast
    }
    tdf <- round(rollapply(tdf,FUN=mean,width=7,align="right"),1)
  }
  
  #plot
  #if there is no forecast data
  if(percentileframe[[1]] == FALSE){
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
      geom_ribbon(aes(ymin=lowerq, ymax=upperq,fill="black"),alpha=.4) +
      geom_line(aes(y=Med),size=0.5,col="red") +
      theme_bw() + xlab("Date") + ylab("Flow (m3/s)") + ggtitle(LakeName) +
      scale_y_continuous(limits=c(min(0,tdf$Obs,na.rm=T),max(tdf$Obs,na.rm=T))) +
      scale_fill_identity(name = '', guide = 'legend',labels = c('50% Conf.','90% Conf.')) +
      scale_colour_manual(name = '', 
                          values =c('black'='black','red'='red'), labels = c('Observed','Modelled \n (Median)')) +
      theme(legend.position=c(0.3,.9),legend.box='horizontal',legend.direction='horizontal',
            legend.text = element_text(size=10), legend.key.size = unit(1, "cm"))
  }
  return(p) 
}



inflowdata <- function(percentileframe,resin_hind,LakeName,m){
  Lookback <- min(nrow(resin_hind$observed.table),14)
  #create timeseries and apply 7-day averaging to minimize wind effects (end-averaging)
  tdf<-merge(Obs=zoo(resin_hind$observed.table[,m],resin_hind$date.time),Est=zoo(resin_hind$estimated.table[,m],resin_hind$date.time))
  
  length_of_forecast <- ncol(percentileframe)

  
  #bind historical and forecast together in a single dataframe
  Observed <- data.frame(t(tail(tdf$Obs,Lookback)))
  Estimated <- data.frame(t(tail(tdf$Est,Lookback)))
  index <- rep(seq_len(nrow(Estimated)), each = 7)
  Estimated<-Estimated[index,]
  
  functionoutput<-rbind(cbind(Estimated,percentileframe),
                        c(unlist(Observed),rep(NA,length_of_forecast)))
  datenames<-as.character(seq(Sys.Date()-Lookback,Sys.Date()+9,1))
  colnames(functionoutput)<-datenames
  rownames(functionoutput)<-paste0(LakeName,c(rownames(percentileframe),"Obs"))
  
  return(functionoutput)
  
}




#main part of script**************************************


#get hindcast
file.resin_hindcast<-file.path(hindcast_directory,model_name,"results", "resin.csv")
resin_hind <-ReadSplCsvWheader(file.resin_hindcast)



#get number of reservoirs in results
num_reservoirs <- length(resin_hind$stations)

#get the files names
file_names <- list.files(path=forecast_directory,pattern = "resin" )

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
m=1
for(m in 1:num_reservoirs){
  if(Forecast == "True" || Forecast == "TRUE" || Forecast == TRUE){
    
    assign(paste0("p",m),inflowplots(percentileframe=MasterPerc[[m]],resin_hind=resin_hind,LakeName=LakeNames[m],m=m,avg=FALSE))
    output<-rbind(output,inflowdata(percentileframe=MasterPerc[[m]],resin_hind=resin_hind,LakeName=LakeNames[m],m))

    
  }else{ #else there is a forecast
    assign(paste0("p",m),inflowplots(percentileframe=FALSE,resin_hind=resin_hind,LakeName=LakeNames[m],m=m,avg=FALSE))
  }

}




#Export plots
resolution = 150
Width = 3000
Height = 2000

png(file.path(output_directory,"Resinflows_1day_1.png"),res=resolution,width=Width,height=Height)
suppressWarnings(multiplot(p1,p2,p3,p4,cols=2))
garbage<-dev.off()

png(file.path(output_directory,"Resinflows_1day_2.png"),res=resolution,width=Width,height=Height)
suppressWarnings(multiplot(p5,p6,p7,cols=2))
garbage<-dev.off()

png(file.path(output_directory,"LOWLS_1day.png"),res=resolution,width=Width/2,height=Height)
suppressWarnings(multiplot(p1,p6,cols=1))
garbage<-dev.off()

#export csv
#copy the reservoir inflow file
#file.copy(file.resin_hindcast,file.path(output_directory,"resin.csv"))

if(Forecast == "True" || Forecast == "TRUE" || Forecast == TRUE){write.csv(output,file.path(output_directory,"Prob_forecast_1day.csv"))}





#now do for 7 day average
if(nrow(resin_hind$observed.table)>7){
  output<-data.frame()
  #loop to plot
  for(m in 1:num_reservoirs){
    if(Forecast == "True" || Forecast == "TRUE" || Forecast == TRUE){
      assign(paste0("p",m),inflowplots(percentileframe=MasterPerc[[m]],resin_hind=resin_hind,LakeName=LakeNames[m],m=m,avg=TRUE))
    }else{
      assign(paste0("p",m),inflowplots(percentileframe = FALSE,resin_hind=resin_hind,LakeName=LakeNames[m],m=m,avg=TRUE))
    }
  
  }
  
  
  #Export plots
  png(file.path(output_directory,"Resinflows_7day_1.png"),res=resolution,width=Width,height=Height)
  suppressWarnings(multiplot(p1,p2,p3,p4,cols=2))
  garbage<-dev.off()
  
  png(file.path(output_directory,"Resinflows_7day_2.png"),res=resolution,width=Width,height=Height)
  suppressWarnings(multiplot(p5,p6,p7,cols=2))
  garbage<-dev.off()
  
  png(file.path(output_directory,"LOWLS_7day.png"),res=resolution,width=Width/2,height=Height)
  suppressWarnings(multiplot(p1,p6,cols=1))
  garbage<-dev.off()
}
  
  
  

