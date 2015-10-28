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
# script_directory<-"C:\\Test_Framework\\EC_Operational_Framework\\Model_Repository\\scripts"


#set working directory and load libraries
setwd(script_directory)
source("rlib/libWATFLOOD_IO.R")
source("rlib/libENSIM_IO.R")
source("rlib/LWSlib.R")

#set directory paths
forecast_directory<-paste0(script_directory,"/../forecast/")
hindcast_directory<-paste0(script_directory,"/../../Repo_hindcast/")
output_directory<-paste0(script_directory,"/../diagnostic/")


#get the files names
file_names<-list.files(path=forecast_directory,pattern = "resin" )

#get number of reservoirs in results
file.resin <- paste0(forecast_directory,file_names[1])
resin <- ReadSplCsvWheader(file.resin)
num_reservoirs<-length(resin$stations)

#Initialize list
emptyframe<-data.frame()
MasterList<- replicate(7,emptyframe,)

#loop through to sort all values by reservoir
for(i in file_names){
  file.resin <- paste0(forecast_directory,i)
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

#get hindcast
file.resin_hindcast<-paste0(hindcast_directory,"wpegr/results/resin.csv")
resin_hind <-ReadSplCsvWheader(file.resin_hindcast)



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
    scale_y_continuous(limits=c(min(0,tdf,na.rm=T),max(tdf,na.rm=T))) +
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
for(m in 1:num_reservoirs){
  assign(paste0("p",m),inflowplots(percentileframe=MasterPerc[[m]],resin_hind=resin_hind,LakeName=LakeNames[m],m=m))
  output<-rbind(output,inflowdata(MasterPerc[[m]],resin_hind,LakeName=LakeNames[m],m))
}


#Export plots
png(paste0(output_directory,"1-dayinflows_1.png"),res=150,width=2000,height=1300)
suppressWarnings(multiplot(p4,p6,p5,p1,cols=2))
garbage<-dev.off()

png(paste0(output_directory,"1-dayinflows_2.png"),res=150,width=2000,height=1300)
suppressWarnings(multiplot(p2,p7,p3,cols=2))
garbage<-dev.off()



#export csv
write.csv(output,paste0(output_directory,"Prob_forecast.csv"))


