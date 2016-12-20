rm(list=ls())



cat("\n Running LWCBtoTB0 Script ********************\n")


#get inputs
args <- commandArgs(TRUE)

# root directory of scripts
cat(paste("1 - ",script_directory <- args[1]),"\n")
# script_directory <-"C:/WR_Ens_dev/A_MS/Repo/scripts"

# template directory
cat(paste("2 - ",template_directory <- args[2],"\n")) 
# template_directory <- "C:/WR_Ens_dev/A_MS/Repo/lib"

# output directory to write tb0's
cat(paste("3 - ",model_directory <- args[3],"\n")) 
# model_directory <- "C:/WR_Ens_dev/A_MS/Repo/wpegr"

#directory name
cat(paste("4 - ",directory_name <- args[4],"\n")) #"diver/level/raing/resrl/strfw/tempg"
# directory_name <- "resrl"

#file type
cat(paste("5 - ",Type <- args[5], "\n")) #"div/level/met/rin/rel/str/tem"
# Type <- "rel"

# start date
cat(paste("6 - ",start_date <- as.Date(args[6]),"\n")) 
# start_date <- as.Date("2013-01-01")
start_year <- as.numeric(format(start_date,"%Y"))

# end date
cat(paste("7 - ",end_date <- as.Date(args[7]),"\n")) 
# end_date <- as.Date("2013-12-31")
end_year <- as.numeric(format(end_date,"%Y"))

# location of LWCB DB
cat(paste("8 - ",DBSource<- args[8],"\n"))
# DBSource<-"Z:/LWS_Db/lwcb.mdb"

#Get string of Station Names and Station numbers
StationNames<- unlist(strsplit(args[9],","))
#StationNames<- c("LOW",149, "LSJ",168, "Namakan_L",172, "LLC",157)
# StationNames <- unlist(strsplit("LOW,76,Rainy,58,Nam,47,Kawish,9001,Winton,9001,Basswoo,9001,Saganag,9001,Kawnipi,9001,Picker,9001,Sturg1,9001,LLC,9001,Vermill,9001,Orr,9001,Quetico,9001,DesMill,9001,RaftL,9001,Valerie,9001,Crooked,9001,Sapawe,9001,CalmLak,9001,Wh_Otte,9001,Lturtle,9001,Otukam,9001,Manit1,9001,NWBay,9001,Dryberr,9001,Atikwa,9001,Rowan,9001,Kakagi,9001",
                                # ","))




#Some set-up stuff#############################

# set working directory to scripts root directory. permits relative path.
setwd(script_directory)

#import libraries
source("rlib/LWSlib.R")

#Set defaults
template_name <- paste0("TEMPLATE_", Type, ".tb0")
file_extension <- tail(unlist(strsplit(DBSource,"[.]")),1)

if(Type == "rel" || Type == "rin" || Type == "str" ){
  NullValue <- -1
  }else{
  NullValue <- -99
  }

# full path for output file
full_output_path = file.path(model_directory,directory_name)




#######Get the Data###############################
#Read TB0
tbo_template <- suppressWarnings(readLines(file.path(template_directory, template_name)))


#Organize the list of stations into a dataframe
if(directory_name=="tempg"){ #need to average max and min if temperature station
  #Put Masterlist in a data.frame
  MasterList<-data.frame(t(matrix(StationNames,nrow=3)),stringsAsFactors=F)
  names(MasterList)<-c("StationNames","MaxT","MinT")
  MasterList$MaxT<-as.numeric(MasterList$MaxT)
  MasterList$MinT<-as.numeric(MasterList$MinT)
  
  }else{
  #Put MasterList in a data.frame
  MasterList<-data.frame(t(matrix(StationNames,nrow=2)),stringsAsFactors=F)
  names(MasterList)<-c("StationNames","Level")
  MasterList$Level<-as.numeric(MasterList$Level)
  }


#Query the database for the station data
AllStations<-xts()
#For loop to get the data of each station and bind to AllStations
if(directory_name=="tempg"){ #need to average max and min if temperature station
  for(i in 1:nrow(MasterList)){
    if(file_extension=="mdb"){AllStations<-cbind.xts(AllStations,MaxMintemp(MasterList[i,2],MasterList[i,3],Range=paste0(start_date,"/"),DBSource=DBSource))}
    if(file_extension=="sqlite"){AllStations<-cbind.xts(AllStations,MaxMintemp(MasterList[i,2],MasterList[i,3],Range=paste0(start_date,"/"),DBSource=DBSource,useSQL=TRUE))}
  }
  }else{
  for(i in 1:nrow(MasterList)){
    if(file_extension=="mdb"){AllStations<-cbind.xts(AllStations,tryCatch(rollapply(LWquery(MasterList[i,2],Range=paste0(start_date,"/"),DBSource=DBSource),width=smooth,FUN=mean,fill="extend",align="right"),error=function(e) LWquery(MasterList[i,2],Range=paste0(start_date,"/"),DBSource=DBSource)))}
    if(file_extension=="sqlite"){AllStations<-cbind.xts(AllStations,tryCatch(rollapply(LWquery(MasterList[i,2],Range=paste0(start_date,"/"),DBSource=DBSource,useSQL=TRUE),width=smooth,FUN=mean,fill="extend",align="right"),error=function(e) LWquery(MasterList[i,2],Range=paste0(start_date,"/"),DBSource=DBSource,useSQL=TRUE)))}
  }
}

#Name of AllStations columns
names(AllStations)<-MasterList[,1]

#subset AllStations by user dates
AllStations<-AllStations[paste0(start_date,"/",end_date)]




#########Write the Data########################

#Define Begining Year
Years<-seq(start_year,end_year,1)

#create directory to store tb0s
dir.create(full_output_path,showWarnings=FALSE)


#Write tb0 for each year
for(i in 1:length(Years)){
  
  #subset object by year
  subData <- AllStations[toString(Years[i])]
  
  #substitute Nullvalue for NA values (default for WATFLOOD)
  subData[is.na(subData)] <- NullValue
  
  #start at the begining date, else start at Jan 1
  if(i==1){
    StartDate <- format(start_date, "%Y/%m/%d")
    StartDateTitle <- format(start_date, "%Y%m%d")
  }else{
    StartDate <- paste0(Years[i], "/01/01")
    StartDateTitle <- paste0(Years[i], "0101")
  }
  
  #substitute metadata if required
  tbo_header <- tbo_template
  tmpdf <- data.frame()
  
  for(j in 1:length(tbo_template)){
    if(grepl(":CreationDate",tbo_header[j])){tbo_header[j] <- format(Sys.time(),":CreationDate %Y/%m/%d %H:%M")}
    if(grepl(":StartDate",tbo_header[j])){tbo_header[j] <- paste0(":StartDate ",StartDate)}
    
    #get column spacing from header
    if(grepl(":ColumnLocation",tbo_header[j]) | grepl(":ColumnName",tbo_header[j]) | grepl(":coeff",tbo_header[j])){
      tmp <- tbo_header[j]
      #need to convert to df because rbind want to convert strings to factors
      #http://stackoverflow.com/questions/1632772/appending-rows-to-a-dataframe-the-factor-problem
      tmp <- t(as.data.frame(unlist(strsplit(tmp,"\\s+")))) 
      tmpdf <- rbind(tmpdf,tmp)
      
    }
       
  }
  
  #import libraries
  source("rlib/LWSlib.R")
  
  colspacing <- print.to.file(tmpdf,Filelink,getcolspace=TRUE)
  colspacing[1] <- 19 #force because :ColumnMetaData row is 18 spaces but only has one column
  
  subData<-cbind(rep(" ",nrow(subData)),data.frame(subData))
  names(subData)[1]<-" "
  
  #Create full file name
  suffix <- tail(unlist(strsplit(template_name, "_")),1)
  Filelink <- file.path(full_output_path,paste0(StartDateTitle,"_", suffix, sep=""))
  
  #Write header to the file
  write(tbo_header, file = Filelink)

  #write data to the file
  print.to.file(subData,Filelink,colspace=colspacing)
  
  
}  
  
  
