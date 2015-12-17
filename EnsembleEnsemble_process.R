#**************************************
#Script to process Ensemble (hyd) Ensemble (met) Data
#comment

rm(list=ls())

#check and install packages if required
list.of.packages <- c("ggplot2")
new.packages <- list.of.packages[!(list.of.packages %in% installed.packages()[,"Package"])]
if(length(new.packages)) install.packages(new.packages,repos='http://cran.us.r-project.org')

#Get arguments
args <- commandArgs(TRUE)
cat(paste("1 - ",script_directory <- args[1]),"\n") #working directory
script_directory <- "C:\\WR_Ensemble\\A_MS\\Repo\\scripts"
ensemble_directory <- "C:\\WR_Ensemble"
output_directory <- file.path(ensemble_directory,"A_MS","Repo","diagnostic")


#set working directory and load libraries
setwd(script_directory)
source("rlib/libWATFLOOD_IO.R")
source("rlib/LWSlib.R")


#build functions
rep.col<-function(x,n){
  matrix(rep(x,each=n), ncol=n, byrow=TRUE)
}
member<-"A_MS"
reservoir <- "LOW"
getmemberdata <-function(member,reservoir){
  #function requires globabl var of 'ensemble_directory'
  #set directory paths
  forecast_directory<-file.path(ensemble_directory,member,"Repo","forecast")
  hindcast_directory<-file.path(ensemble_directory,member,"Repo_hindcast")
  
  #get the files names
  file_names <- list.files(path=forecast_directory,pattern = "resin" )
  num_metcasts <- length(file_names)
  
  #get 1st member hindcast
  hind <- ReadSplCsvWheader(file.path(hindcast_directory,"wpegr","results","resin.csv"))
  hindcast <-rep.col(c(hind$estimated.table[,reservoir],rep(NA,10)),num_metcasts)
  
  #get observed data
  inflows <- data.frame(Date=c(hind$date.time,seq(tail(hind$date.time+1,n=1),by = 1, length.out=10)),
                        Obs=c(hind$observed.table[,reservoir],rep(NA,10)))
  
  #Calculate Bias
  bias_days <- 14
  obs_inflows <- mean(inflows$Obs[(length(inflows$Obs)-bias_days-10):(length(inflows$Obs)-10)])
  mod_inflows <- mean(hindcast[,1][(length(inflows$Obs)-bias_days-10):(length(hindcast[,1])-10)])
  bias <- mod_inflows - obs_inflows

  
  #loop through to sort all values by reservoir
  i=1
  for(i in 1:num_metcasts){
    file.resin <- file.path(forecast_directory,file_names[i])
    resin <- ReadSplCsvWheader(file.resin)
    hindcast[(nrow(hindcast)-9):nrow(hindcast),i] <- resin$estimated.table[,reservoir]
  }
  hindcast[(nrow(hindcast)-bias_days-10):nrow(hindcast),] <- hindcast[(nrow(hindcast)-bias_days-10):nrow(hindcast),] - bias
  return(hindcast)
}

#first get observed data
hindcast_directory<-paste0(script_directory,"/../../Repo_hindcast/")
#get hindcast
file.resin_hindcast<-paste0(hindcast_directory,"wpegr/results/resin.csv")
resin_hind <- ReadSplCsvWheader(file.resin_hindcast)
num_reservoirs<-length(resin_hind$stations)

members <- c("A_MS","B","C","D","E")
reservoir <- "LOW"
#members <- members[1]
getreservoirdata <- function(members,reservoir){
  #requires resin_hind and ensemble_directory global vars
  #build basefile
  inflows <- data.frame(Date=c(resin_hind$date.time,seq(tail(resin_hind$date.time+1,n=1),by = 1, length.out=10)),
                          Obs=c(resin_hind$observed.table[,reservoir],rep(NA,10)))

  model_output <- lapply(members,getmemberdata,reservoir=reservoir)
  model_output <- do.call(data.frame,model_output)
  model_percentiles <- t(apply(model_output,1,quantile,probs=c(0.05,0.25,0.5,0.75,0.95)))
  

  output_df <- data.frame(inflows,model_percentiles)
  return(output_df)
}

LOW <- getreservoirdata(members,"LOW")
LS <- getreservoirdata(members,"LS")

# library(xts)
# LS.ts <- xts(LS[,-1],as.Date(LS[,1]))
# LS.3day <- rollmean(LS.ts, 3)
# LS.3day <- data.frame(Date=as.Date(index(LS.3day)),LS.3day)
# LS.3day$Date<-as.Date(row.names(LS.3day))




ensembleplot <- function(forecast_frame){
  name <- deparse(substitute(forecast_frame))
  p   <-  ggplot(data=forecast_frame,aes(x=Date)) +
    geom_line(aes(y = Obs,col="black"),size=0.5) +
    #geom_line(aes(y=Est,col="red"),size=0.5) +
    geom_ribbon(aes(ymin=X5.,ymax=X95.,fill="dimgray"),alpha=.4) +
    geom_line(aes(y=X50.),size=0.5,col="red") +
    theme_bw() + xlab("Date") + ylab("1-Day Inflow (m3/s)") + ggtitle(name) +
    scale_y_continuous(limits=c(min(0,forecast_frame$Obs,na.rm=T),max(forecast_frame$Obs,na.rm=T))) +
    scale_fill_identity(name = '', guide = 'legend',labels = c('90% Conf.')) +
    scale_colour_manual(name = '', 
                        values =c('black'='black','red'='red'), labels = c('Observed','Modelled \n (Median)')) +
    theme(legend.position=c(0.3,.9),legend.box='horizontal',legend.direction='horizontal')
  p
}

p1 <- ensembleplot(LOW)
p2 <- ensembleplot(LS)

png(paste0(output_directory,"/EE.png"),res=150,width=1000,height=1300)
suppressWarnings(multiplot(p1,p2,cols=1))
garbage<-dev.off()


write.csv(cbind(LOW,LS),file.path(output_directory,"Ensemble_Prob_Forecast.csv"))



