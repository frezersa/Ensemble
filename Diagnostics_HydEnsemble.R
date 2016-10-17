#*****************************************
#Script to process multiple WATFLOOD met-ensemble forecasts, creating an 'ensemble of ensembles'
#that captures the hydrological, bias correction, and meterological uncertainty.
#written by: James Bomhof
#date: 2016.01.11
#******************************************
rm(list=ls())

#check and install packages if required
list.of.packages <- c("ggplot2","zoo","xts","RODBC","grid")
new.packages <- list.of.packages[!(list.of.packages %in% installed.packages()[,"Package"])]
if(length(new.packages)) install.packages(new.packages,repos='http://cran.us.r-project.org')
require(grid)


#Get arguments
args <- commandArgs(TRUE)
cat(paste("1 - ",script_directory <- args[1]),"\n") #working directory
cat(paste("1 - ",forecast_directory <- args[2]),"\n") #forecast directory
# script_directory <- "Q:\\WR_Ens_dev\\A_MS\\Repo\\scripts"
# forecast_directory <- "Q:\\WR_Ens_dev\\HydForecastStorage\\forecast_20161017"


#set working directory and load libraries
setwd(script_directory)
source("rlib/libWATFLOOD_IO.R")
source("rlib/libENSIM_IO.R")
source("rlib/LWSlib.R")
library(plyr)


#Define Functions***************************************************************

substrRight <- function(x, n){
  #gets the right side of a string
  #
  #Args:
  #   x: original string
  #   y: the number of characters you wish to retrieve
  #
  #Returns:
  #   The right subset of the string
  
  substr(x, nchar(x)-n+1, nchar(x))
}


getsingleforecast <- function(file_name, reservoir){
  #retrieves the modelled forecast for a single reservoir
  #
  #Args:
  #   file_name: the location of the resin.csv file
  #   reservoir: the number of a reservoir in the resin file (typically a value between 1-7)
  #
  #Returns:
  #   a vector of the forecast reservoir inflows
  
  resin <- ReadSplCsvWheader(file_name)
  output <- resin$estimated.table[,reservoir]
  return(output)
}


getmetensembleforecast <- function(reservoir = 1, file_paths){
  # gets multiple forecasts for a single reservoir and combines them in a dataframe
  # uses function getsingleforecast() in a lapply loop
  #
  #Args:
  #   reservoir: the number of a reservoir in the resin file (typically a value between 1-7)
  #   file_paths: a vector of strings denoting the paths to each resin.csv file
  #
  #Returns:
  #   a dataframe of the forecasts for a specific reservoir, each row refers to a day
  #   in the forecast, each column is a different forecast
  
  forecast.list <- lapply(file_paths,getsingleforecast,reservoir=reservoir)
  forecast.df <- do.call(rbind,forecast.list)
  return(forecast.df)
}


getbias <- function(lookback = 3, reservoir = 1, hindcast){
  # calculates the bias between the observed and modelled for a single reservoir
  #
  #Args:
  #   lookback: integer; the number of days on which to calculate the bias
  #   reservoir: the number of a reservoir in the resin file (typically a value between 1-7)
  #   hindcast: R-object containing the hindcast modelled data
  #
  #Returns:
  #   a float; the bias between observed and hindcast for specified lookback
  
  daysinhindcast <-nrow(hindcast$observed.table)
  observed <- hindcast$observed.table[(daysinhindcast-lookback+1):daysinhindcast,reservoir]
  estimated <- hindcast$estimated.table[(daysinhindcast-lookback+1):daysinhindcast,reservoir]
  bias <- mean(observed) - mean(estimated) #positive means observed is higher than estimated
  return(bias)
}


applyreservoirbias <-  function(lookback,reservoir,hindcast,forecast){
  # calculates a new bias-corrected forecast, uses the getbias() function
  #
  #Args:
  #   lookback: integer; the number of days on which to calculate the bias
  #   reservoir: the number of a reservoir in the resin file (typically a value between 1-7)
  #   hindcast: R-object containing the hindcast data
  #   forecast: R-object containing the forecast data
  #
  #Returns:
  # bias corrected forecast
  
  bias <- getbias(lookback, reservoir, hindcast)
  forecast.reservoir <- forecast[[reservoir]] + bias
  return(forecast.reservoir)
}


getbiasedforecasts <- function(reservoir,hindcast,forecast){
  # calculates a new bias-corrected forecast using multiple lookback periods (hardcoded),
  # uses the applyreservoirbias() function
  #
  #Args:
  #   reservoir: the number of a reservoir in the resin file (typically a value between 1-7)
  #   hindcast: R-object containing the hindcast data
  #   forecast: R-object containing the forecast data
  #
  #Returns:
  # dataframe of bias corrected forecasts based on multiple lookbacks
  # the hindcast is appended to each forecast and goes back in time
  # for as many days as the forecast
  # each row refers to a day, each column is a bias-corrected forecast
  
  rep.row<-function(x, n){
    matrix(rep(x, each = n),nrow = n)
  }
  
  ensembleforecast.list <- lapply(c(3, 7, 12), applyreservoirbias, reservoir, hindcast, forecast)
  ensembleforecast.df <- do.call(rbind,ensembleforecast.list)
  
  #append hindcast MODELLED data
  rows <- nrow(ensembleforecast.df)
  hindcast_append <- rep.row(hindcast$estimated.table[[reservoir]], rows)
  ensembleforecast.df <- as.data.frame(cbind(hindcast_append, ensembleforecast.df))
  #apply dates for the row names
  names(ensembleforecast.df) <- seq(from = hindcast$date.time[1], to = hindcast$date.time[length(hindcast$date.time)] + 10, by = 1)
  
  return(ensembleforecast.df)
}


getbiasedmembers <- function(member, forecast_directory){
  # get the bias corrected forecasts for each reservoir in a single hydrological
  # ensemble member
  #
  #Args:
  #   member: string; the name of the hydrological ensemble member (ex. "A_MS")
  #   forecast_directory: string; path to where ensemble forecasts have been stored
  #
  #Returns:
  #   list of dataframes; each dataframes contains the bias-corrected forecasts for each met ensemble
  #   Each row refers to a data in the hindcast/forecast
  #   each column refers to a different bias-corrected forecast
  
  #define file paths
  member_directory <- file.path(forecast_directory, member)
  file_names <- list.files(path=member_directory,pattern = paste0("resin","[0-9]" ))
  file_paths <- file.path(member_directory, file_names)
  
  hindcast_name <- list.files(path=member_directory, pattern = paste0("resin","_" ))
  hindcast_path <- file.path(member_directory, hindcast_name)
  
  #get the forecast
  forecast <- lapply(1:7, getmetensembleforecast, file_paths=file_paths)
  names(forecast) <- ReadSplCsvWheader(file_paths[1])$stations
  
  #get the hindcast
  hindcast <- ReadSplCsvWheader(hindcast_path)
    
  #apply bias corrections to the forecast
  newforecast <- lapply(1:7, getbiasedforecasts, hindcast, forecast)
  names(newforecast) <- hindcast$stations
  
  return(newforecast)
}


combinemembers <- function(allmembers){
  # combines the bias corrected hindcasts/forecasts from each hydrological ensemble member
  # currently only allows 11 hydrological ensemble members
  #
  #Args:
  #   allmembers: list of hydrological ensemble members, each member contains another list that
  #   was generated from getbiasedmembers()
  #Returns:
  #   list of dataframes; each dataframes contains the bias-corrected forecasts for all met ensembles
  #   Each row refers to a data in the hindcast/forecast
  #   each column refers to a different bias-corrected forecast
  
  num_members <- length(allmembers)
  if(num_members == 1){result = mapply(rbind,allmembers[[1]],SIMPLIFY = FALSE)}
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


getpercentile <- function(df){
  # calculates the percentiles of a forecast
  #
  #Args:
  #   df: dataframe containing the hindcast/forecast, each row refers to a distinct day
  #       each column is a separate forecast
  #
  #Returns:
  #   dataframe of percentiles, each row refers to a distinct day
  
  probs=c(0,.05,.25,.5,.75,.95,1)
  output.df <- apply(df,2,quantile,probs=probs)
  return(output.df)
}


getforecastpercentile <- function(forecast_member,member_name){
  # calcultes the percentiles for every reserveroir and hyd. ensemble
  #
  #Args:
  #   forecast_member: list containing a dataframes for each reservoir,
  #                    dataframe contains all the hindcasts/forecasts
  #   member_name: string specifying the hyd. ensemble member
  #
  #Returns:
  #   dataframe containing percentiles for the complete hindcast and forecast
  #   for all the reservoirs

  #calculate percentile for each day and each reservoir
  output.list <- lapply(forecast_member,getpercentile)
  
  # convert percentiles to long form
  output.df <- melt(output.list,id.vars=rownames(output.list))
  output.df <- data.frame(Day=as.Date(output.df[,2]),
                          Value = output.df[,3],
                          Config = rep(member_name,nrow(output.df)),
                          Perc = output.df[,1],
                          Res = output.df[,4])
  
  #convert to short form that contains all the data for every reservoir
  output.df <- dcast(output.df, Day + Config + Res ~ Perc, value.var = "Value")
  names(output.df) <- paste0("x",gsub("%","",names(output.df)))
  
  output <- list(output.df)
}


list.dirs <- function(path=".", pattern = NULL, all.dirs=FALSE,
                      full.names = FALSE, ignore.case = FALSE) {
  # function to list only the directories in a given folder
  # http://stackoverflow.com/questions/4749783/how-to-obtain-a-list-of-directories-within-a-directory-like-list-files-but-i
  #
  #Args:
  #   path: string; path to directory where you want to find all the folders
  #   others: I only use the defaults
  #
  #Returns:
  #   vector of folder names within directory
  
  # use full.names=TRUE to pass to file.info
  all <- list.files(path, pattern, all.dirs,
                    full.names=TRUE, recursive=FALSE, ignore.case)
  dirs <- all[file.info(all)$isdir]
  # determine whether to return full names or just dir names
  if(isTRUE(full.names))
    return(dirs)
  else
    return(basename(dirs))
}


gethindcast <- function(member, forecast_directory){
  # get the resin hindcast of a given member
  #
  #Args:
  #   member: string; the name of the hydrological ensemble member (ex. "A_MS")
  #   forecast_directory: string; path to where ensemble forecasts have been stored
  #
  #Returns:
  #   reservoir inflow hindcast
  
  #define file paths
  member_directory <- file.path(forecast_directory, member)
  hindcast_name <- list.files(path=member_directory, pattern = paste0("resin","_" ))
  hindcast_path <- file.path(member_directory, hindcast_name)
  
  #get the hindcast
  hindcast <- ReadSplCsvWheader(hindcast_path)
  
  return(hindcast)
}


#plot
inflowplot <- function(member.plot){
  p <- ggplot(data=member.plot, aes_string(x="xDay",y="x50",ymin="x5",ymax="x95")) +
    
    #90th percentile forecast
    geom_ribbon(data=member.plot[member.plot$xConfig=="All" & member.plot$xDay>=forecast_date,],aes(fill="5%-95%")) +
    
    #50th percentile forecast
    geom_ribbon(data=member.plot[member.plot$xConfig=="All" & member.plot$xDay>=forecast_date,],aes_string(fill="'25%-75%'",ymin="x25",ymax="x75")) +
    
    #median forecast
    geom_line(data=member.plot[member.plot$xConfig=="All" & member.plot$xDay>=forecast_date,],aes(col="Med")) +
    
    #observed hindcast
    geom_line(data=member.plot[member.plot$xConfig=="All" & member.plot$xDay<forecast_date,],aes(y = Observed, col="Obs")) +
    
    #modelled hindcast 1
    geom_line(data=member.plot[member.plot$xConfig=="A_MS",],aes(col="Mod1")) +
    
    #modelled hindcast 2
    geom_line(data=member.plot[member.plot$xConfig=="50B",],aes(col="Mod2")) +
    
    #vertical line at forecast  
    geom_vline(xintercept=as.numeric(forecast_date),col="gray40") +
      
    #attributes  
    theme_bw() + xlab("Date") + ylab("1-Day Inflow (m3/s)") + ggtitle(member.plot$xRes[1]) +
    scale_y_continuous(limits=c(min(c(member.plot$x50,member.plot$x5)),max(c(member.plot$x50,member.plot$x95),na.rm=T))) +
    scale_fill_manual(name = '', values=c('gray25','gray50')) +
    scale_colour_manual(name = '',
                        values =c('Med' = 'red','Obs'='black','Mod1'='#41b6c4','Mod2'='#225ea8')) +
    theme(legend.position=c(0.0,0.7),legend.justification=c(0,0),legend.box.just="left",legend.box='vertical',legend.direction='horizontal',
          legend.key.size=unit(.4,"cm"),panel.grid.major=element_line(colour="#808080",size=0.4))
  
  
  
  return(p)
}





#Main Script******************************************************************************
#membernames <- c("A_MS","50B","50C","50D","50E","50F","50G","50H","51A","51B","51C")
membernames <- list.dirs(forecast_directory) #get lst of hyd. ensembles

# get the bias corrected forecasts for each reservoir for all hyd ensemble members
allmembers.list <- lapply(membernames,getbiasedmembers,forecast_directory)

#get all the raw data into single output
allmembers <- combinemembers(allmembers.list)

#calculate percentiles from all the forecasts
combinedforecast <- getforecastpercentile(allmembers,"All")[[1]]

#calculate percentiles on individual forecasts
members.long <- mapply(getforecastpercentile,allmembers.list,membernames)
members.long <- do.call(rbind,members.long)
members.long <- rbind(members.long,combinedforecast)

#get observed data
hindcast <- gethindcast(membernames[1],forecast_directory)
obs.ts <- xts(hindcast$observed, order.by = as.Date(hindcast$date))
res_names <- hindcast$stations

forecast_date <- as.Date(substrRight(forecast_directory,8),format="%Y%m%d")
empty.ts <- xts(,order.by = seq(forecast_date,forecast_date+9,1))

obs.filled <- merge(obs.ts,empty.ts)
obs <- data.frame(Date = index(obs.filled), obs.filled)

obs.long <- melt(obs,id.vars = names(obs)[1])
names(obs.long) <- c("xDay","xRes","Observed")


#merge the modelled and observed together
members.long <- merge(members.long,obs.long,by = c("xDay","xRes"))


if(membernames > 1){
  m=1
  for(m in 1:7){
    member.plot <- members.long[members.long$xRes==res_names[m],]
    assign(paste0("p",m),inflowplot(member.plot))
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
  
  
  
  
  #export to csv (in consistent format to old forecasts)
  output <- data.frame()
  for(n in 1:7){
    #get the observed and modelled data for each reservoir
    member.data <- members.long[members.long$xRes==res_names[n] & members.long$xConfig=="All" & members.long$xDay>(forecast_date-15),]

    #remove some of the attribute data and modify format
    tmp <-data.frame(t(member.data[,c(-1:-3)]))
    rownames(tmp) <- paste0(res_names[n],rownames(tmp))
    colnames(tmp) <- member.data$xDay
    output <- rbind(output,tmp)
  }
  names(output) <- member.data$xDay
  
  #export csv
  write.csv(output,file.path(forecast_directory,"Prob_Forecast_AllEnsembles_BiasCorr.csv"))
}
