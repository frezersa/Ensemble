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

cat(paste("2 - ",model_directory <- args[2]),"\n") #typically 'wpegr'
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



inflowdata <- function(percentileframe,resin_hind,LakeName,m){
  Lookback<-min(14,nrow(resin_hind$observed.table))
  
  
  #find bias for hindcast
  #create timeseries and apply 7-day averaging to minimize wind effects (end-averaging)
  tdf<-merge(Obs=zoo(resin_hind$observed.table[,m],resin_hind$date.time),Est=zoo(resin_hind$estimated.table[,m],resin_hind$date.time))
  
  if(Lookback>14){
    tdf.7day<-round(rollapply(tdf,FUN=mean,width=7,align="right"),1)
    
    #calculate bias (as per thesis from Dominique Bourdin, UBC 2013)
    tdf.7daytail<-tail(tdf.7day,n=Lookback) #use last 14 days, this is somewhat aribitrary
    bias<-(sum(tdf.7daytail$Est)-sum(tdf.7daytail$Obs))/Lookback
    
  }
  
  percentileframe.biascorr<-percentileframe
  
  #bind historical and forecast together in a single dataframe
  Observed<-data.frame(t(tail(tdf$Obs,Lookback)))
  index <- rep(seq_len(nrow(Observed)), each = 7)
  Observed<-Observed[index, ]
  
  functionoutput<-cbind(Observed,percentileframe.biascorr)
  datenames<-as.character(seq(Sys.Date()-Lookback,Sys.Date()+9,1))
  colnames(functionoutput)<-datenames
  rownames(functionoutput)<-paste0(LakeName,rownames(percentileframe))
  
  return(functionoutput)
  
}




#main part of script**************************************


#get hindcast
file.resin_hindcast<-file.path(hindcast_directory,model_directory,"results", "resin.csv")
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
for(m in 1:num_reservoirs){
  if(Forecast == "True" || Forecast == "TRUE" || Forecast == TRUE){
    assign(paste0("p",m),inflowplots(percentileframe=MasterPerc[[m]],resin_hind=resin_hind,LakeName=LakeNames[m],m=m,avg=FALSE))
    output<-rbind(output,inflowdata(MasterPerc[[m]],resin_hind,LakeName=LakeNames[m],m))
  }else{ #else there is a forecast
    assign(paste0("p",m),inflowplots(percentileframe=FALSE,resin_hind=resin_hind,LakeName=LakeNames[m],m=m,avg=FALSE))
  }

}


#Export plots
png(file.path(output_directory,"Resinflows_1day_1.png"),res=150,width=2000,height=1300)
suppressWarnings(multiplot(p4,p6,p5,p1,cols=2))
garbage<-dev.off()

png(file.path(output_directory,"Resinflows_1day_2.png"),res=150,width=2000,height=1300)
suppressWarnings(multiplot(p2,p7,p3,cols=2))
garbage<-dev.off()

png(file.path(output_directory,"LOWLS_1day.png"),res=150,width=1000,height=1300)
suppressWarnings(multiplot(p1,p2,cols=1))
garbage<-dev.off()

#export csv
if(Forecast == "True" || Forecast == "TRUE" || Forecast == TRUE){write.csv(output,file.path(output_directory,"Prob_forecast_1day.csv"))}






#now do for 7 day average
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
png(file.path(output_directory,"Resinflows_7day_1.png"),res=150,width=2000,height=1300)
suppressWarnings(multiplot(p4,p6,p5,p1,cols=2))
garbage<-dev.off()

png(file.path(output_directory,"Resinflows_7day_2.png"),res=150,width=2000,height=1300)
suppressWarnings(multiplot(p2,p7,p3,cols=2))
garbage<-dev.off()

png(file.path(output_directory,"LOWLS_7day.png"),res=150,width=1000,height=1300)
suppressWarnings(multiplot(p1,p2,cols=1))
garbage<-dev.off()




