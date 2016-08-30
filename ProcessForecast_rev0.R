#*****************************************
#Script to process multiple WATFLOOD met-ensemble forecasts, creating an 'ensemble of ensembles'
#that captures the hydrological, bias correction, and meterological uncertainty.
#written by: James Bomhof
#date: 2016.01.11
#******************************************
rm(list=ls())

#check and install packages if required
list.of.packages <- c("ggplot2","zoo","xts","RODBC")
new.packages <- list.of.packages[!(list.of.packages %in% installed.packages()[,"Package"])]
if(length(new.packages)) install.packages(new.packages,repos='http://cran.us.r-project.org')

#Get arguments
args <- commandArgs(TRUE)
cat(paste("1 - ",script_directory <- args[1]),"\n") #working directory
cat(paste("1 - ",forecast_directory <- args[2]),"\n") #forecast directory
#script_directory <- "C:/Users/JMB/Documents/R/RLibrary"
#forecast_directory <- "C:/Users/JMB/Documents/R/RLibrary/ForecastProcessing/HydForecastStorage/forecast_20160111"



#set working directory and load libraries
setwd(script_directory)
source("rlib/libWATFLOOD_IO.R")
source("rlib/libENSIM_IO.R")
source("rlib/LWSlib.R")


getsingleforecast <- function(file_name,reservoir){
  resin <- ReadSplCsvWheader(file_name)
  output <- resin$estimated.table[,reservoir]
  return(output)
}

getmetensembleforecast <- function(reservoir=1,file_paths){
  forecast.list <- lapply(file_paths,getsingleforecast,reservoir=reservoir)
  forecast.df <- do.call(rbind,forecast.list)
  return(forecast.df)
}


getbias <- function(lookback=3,reservoir=1,hindcast){
  daysinhindcast <-nrow(hindcast$observed.table)
  observed <- hindcast$observed.table[(daysinhindcast-lookback+1):daysinhindcast,reservoir]
  estimated <- hindcast$estimated.table[(daysinhindcast-lookback+1):daysinhindcast,reservoir]
  bias <- mean(observed) - mean(estimated) #positive means observed is higher than estimated
  return(bias)
}

applyreservoirbias <-  function(lookback,reservoir,hindcast,forecast){
  bias <- getbias(lookback, reservoir, hindcast)
  forecast.reservoir <- forecast[[reservoir]] + bias
}

getbiasedforecasts <- function(reservoir,hindcast,forecast){
  ensembleforecast.list <- lapply(c(3,5,10),applyreservoirbias,reservoir,hindcast,forecast)
  ensembleforecast.df <- do.call(rbind,ensembleforecast.list)
  return(ensembleforecast.df)
}


getbiasedmembers <- function(member,forecast_directory){
  #define file paths
  member_directory <- file.path(forecast_directory,member)
  file_names <- list.files(path=member_directory,pattern = paste0("resin","[0-9]" ))
  file_paths <- file.path(member_directory,file_names)
  
  hindcast_name <- list.files(path=member_directory,pattern = paste0("resin","_" ))
  hindcast_path <- file.path(member_directory,hindcast_name)
  #get the forecast
  forecast <- lapply(1:7,getmetensembleforecast,file_paths=file_paths)
  names(forecast) <- ReadSplCsvWheader(file_paths[1])$stations
  
  #get the hindcast
  hindcast <- ReadSplCsvWheader(hindcast_path)
    
  #apply bias corrections to the forecast
  newforecast <- lapply(1:7,getbiasedforecasts,hindcast,forecast)
  names(newforecast) <-hindcast$stations
  
  return(newforecast)
}

combinemembers <- function(allmembers){
  num_members <- length(allmembers)
  if(num_members == 1){result = allmembers}
  if(num_members == 2){result = mapply(rbind,allmembers[[1]],allmembers[[2]],SIMPLIFY=FALSE)}
  if(num_members == 3){result = mapply(rbind,allmembers[[1]],allmembers[[2]],allmembers[[3]],SIMPLIFY=FALSE)}
  if(num_members == 4){result = mapply(rbind,allmembers[[1]],allmembers[[2]],allmembers[[3]],allmembers[[4]],SIMPLIFY=FALSE)}
  if(num_members == 5){result = mapply(rbind,allmembers[[1]],allmembers[[2]],allmembers[[3]],allmembers[[4]],allmembers[[5]],SIMPLIFY=FALSE)}
  if(num_members == 6){result = mapply(rbind,allmembers[[1]],allmembers[[2]],allmembers[[3]],allmembers[[4]],allmembers[[5]],allmembers[[6]],SIMPLIFY=FALSE)}
  if(num_members == 7){result = mapply(rbind,allmembers[[1]],allmembers[[2]],allmembers[[3]],allmembers[[4]],allmembers[[5]],allmembers[[6]],allmembers[[7]],SIMPLIFY=FALSE)}
  if(num_members == 8){result = mapply(rbind,allmembers[[1]],allmembers[[2]],allmembers[[3]],allmembers[[4]],allmembers[[5]],allmembers[[6]],allmembers[[7]],allmembers[[8]],SIMPLIFY=FALSE)}
  if(num_members == 9){result = mapply(rbind,allmembers[[1]],allmembers[[2]],allmembers[[3]],allmembers[[4]],allmembers[[5]],allmembers[[6]],allmembers[[7]],allmembers[[8]],allmembers[[9]],SIMPLIFY=FALSE)}
  if(num_members == 10){result = mapply(rbind,allmembers[[1]],allmembers[[2]],allmembers[[3]],allmembers[[4]],allmembers[[5]],allmembers[[6]],allmembers[[7]],allmembers[[8]],allmembers[[9]],allmembers[[10]],SIMPLIFY=FALSE)}
  if(num_members == 11){result = mapply(rbind,allmembers[[1]],allmembers[[2]],allmembers[[3]],allmembers[[4]],allmembers[[5]],allmembers[[6]],allmembers[[7]],allmembers[[8]],allmembers[[9]],allmembers[[10]],allmembers[[11]],SIMPLIFY=FALSE)}
  
  return(result)
}

membernames <- c("A_MS","50B","50C","50D","50E","50F","50G","50H","51A","51B","51C")
allmembers.list <- lapply(membernames,getbiasedmembers,forecast_directory)


allmembers <- combinemembers(allmembers.list)

#plot
probs=c(0,.05,.25,.5,.75,.95,1)
MasterPerc<-list()
for(k in 1:length(allmembers)){
  MasterPerc[[k]]<-apply(allmembers[[k]],2,quantile,probs=probs)
}

member_directory <- file.path(forecast_directory,"A_MS")

hindcast_name <- list.files(path=member_directory,pattern = paste0("resin","_" ))
hindcast_path <- file.path(member_directory,hindcast_name)
resin_hind <-ReadSplCsvWheader(hindcast_path)

LakeNames<-c("Lake of the Woods", "Lac Seul", "Lake St. Joseph", "Lac La Croix", "Namakan Lake", "Rainy Lake", "Caribou Falls")
shortnames<-c("LOW","LS","LSJ","LLC","Nam","Rainy","Car")

#define plotting function
inflowplots <- function(percentileframe,resin_hind,LakeName,m){
  #    m<-1
  #    percentileframe<-MasterPerc[[m]]
  #    LakeName<-LakeNames[m]
  Lookback<-min(14,nrow(resin_hind$observed.table))
  
  #find bias for hindcast
  #create timeseries and apply 7-day averaging to minimize wind effects (end-averaging)
  tdf<-merge(Obs=zoo(resin_hind$observed.table[,m],resin_hind$date.time),Est=zoo(resin_hind$estimated.table[,m],resin_hind$date.time))
  
  if(Lookback>14){
    tdf.7day<-round(rollapply(tdf,FUN=mean,width=7,align="right"),1)
    
    #calculate bias 
    tdf.7daytail<-tail(tdf.7day,n=Lookback) #use last 14 days, this is somewhat aribitrary
    bias<-(sum(tdf.7daytail$Est)-sum(tdf.7daytail$Obs))/Lookback
    #   percentileframe<-percentileframe - bias
  }
  
  #create data frame for ggplot to work with
  futuredates<-tail(resin_hind$date.time,n=1) + c(1:10)
  tdf<-merge(Obs=zoo(resin_hind$observed.table[,m],resin_hind$date.time),Est=zoo(resin_hind$estimated.table[,m],resin_hind$date.time),
             Min=zoo(percentileframe[c(2),],futuredates),Max=zoo(percentileframe[c(6),],futuredates),Med=zoo(percentileframe[c(4),],futuredates))
  #subset
  #tdf<-window(tdf,start=as.Date("2014-08-15"))
  
  #plot
  p   <-  ggplot(data=fortify(tdf),aes(x=Index)) +
    geom_line(aes(y = Obs,col="black"),size=0.5) +
    geom_line(aes(y=Est,col="red"),size=0.5) +
    geom_ribbon(aes(ymin=Min,ymax=Max,fill="dimgray"),alpha=.4) +
    geom_line(aes(y=Med),size=0.5,col="red") +
    theme_bw() + xlab("Date") + ylab("1-Day Inflow (m3/s)") + ggtitle(LakeName) +
    scale_y_continuous(limits=c(min(0,tdf$Obs,na.rm=T),max(tdf$Est,tdf$Obs,na.rm=T))) +
    scale_fill_identity(name = '', guide = 'legend',labels = c('90% Conf.')) +
    scale_colour_manual(name = '', 
                        values =c('black'='black','red'='red'), labels = c('Observed','Modelled \n (Median)')) +
    theme(legend.position=c(0.3,.9),legend.box='horizontal',legend.direction='horizontal')
  p   
  return(p) 
}

# 
# t<-inflowplots(MasterPerc[[1]],resin_hind,LakeName=LakeNames[1],1)
#   t

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
    
    
    
    #apply bias correction to forecast
    #percentileframe.biascorr<-percentileframe - bias
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


output<-data.frame()
#loop to plot
for(m in 1:7){
  assign(paste0("p",m),inflowplots(percentileframe=MasterPerc[[m]],resin_hind=resin_hind,LakeName=LakeNames[m],m=m))
  output<-rbind(output,inflowdata(MasterPerc[[m]],resin_hind,LakeName=LakeNames[m],m))
}


#Export plots
png(file.path(forecast_directory,"1-dayinflows_1.png"),res=150,width=2000,height=1300)
suppressWarnings(multiplot(p4,p6,p5,p1,cols=2))
garbage<-dev.off()

png(file.path(forecast_directory,"1-dayinflows_2.png"),res=150,width=2000,height=1300)
suppressWarnings(multiplot(p2,p7,p3,cols=2))
garbage<-dev.off()

png(file.path(forecast_directory,"LWLS.png"),res=150,width=1000,height=1300)
suppressWarnings(multiplot(p1,p2,cols=1))
garbage<-dev.off()



#export csv
write.csv(output,file.path(forecast_directory,"Prob_forecast.csv"))
