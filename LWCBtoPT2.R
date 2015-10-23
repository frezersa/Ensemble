#***********************************
#comment
#Name:LWCBtoPT2
#Written On: October 24, 2013
#Written By: James Bomhof
#Description: Script to create *_ill.pt2 file which is required for WATFLOOD initial lake levels. 
#The script queries the database (.mdb or .sqlite) and fills in the lake levels where possible.
#***********************************
# #levels stations
# StationNames=c("Warroad(SS)_LW",68,
#                "Shoal_Lake_LW",280,
#                "ClearWater_LW",72,
#                "Hanson_LW",70,
#                "Cyclone_LW",71,
#                "Keewatin_LW",73,
#                "LS_Post_LS",14,
#                "Hudson_LS",13,
#                "GoldPines_LS",15,
#                "FF_RL",57,
#                "NorthWest_Bay_RL",251,
#                "Bear_Pass_RL",131,
#                "Boundary_Falls_WR",257,
#                "Minaki_WR",78,
#                "Pakwash",197,
#                "LSJ_Diversion",4,
#                "LacdesMilleLacs",250,
#                "Kettle_Falls_NL",43,
#                "Campbells_Camp_LLC",39)

rm(list=ls())
cat("\n Running LWCBtoPT2 Script ********************\n")

# ======= inputs
#
#= command line arguments
# only want arguments after --args
args <- commandArgs(TRUE)

#= variable mappings
# root directory of scripts in ..\writeTB0's
cat(paste("1 -",script_directory <- args[1],"\n"))
#script_directory<- "C:/Build_Framework/EC_Operational_Framework/Model_Repository/scripts"
setwd(script_directory)

#get parent directory
setwd("..")
parent_directory <- getwd()
setwd(script_directory)
model_directory <- paste0(parent_directory,"/wpegr")
lib_directory <- paste0(parent_directory,"/lib")

cat(paste("2 - ",directory_name <- args[2],"\n")) #level
#directory_name <- "level"
full_output_path = file.path(model_directory,directory_name)

cat(paste("3 - ", Type <-args[3], "\n")) #level
#Type<-"level"

# Date Query
cat(paste("4 - ",query.date <- toString(as.Date(args[4])),"\n"))
#query.date <- toString(as.Date("2012/01/01"))

# location of LWCB DB
cat(paste("5 - ",DBSource<- args[5],"\n"))
#DBSource<-"Z:/LWS_Db/lwcb.mdb"


#= import libraries
# set working directory to scripts root directory. permits relative path.
setwd(script_directory)
source("rlib/LWSlib.R")

file_extension<-file_ext(DBSource)

#check and install packages if required
list.of.packages <- c("gdata")
new.packages <- list.of.packages[!(list.of.packages %in% installed.packages()[,"Package"])]
if(length(new.packages)) install.packages(new.packages,repos='http://cran.us.r-project.org')

suppressMessages(library(gdata))

#get PTO template
template<-readLines(paste0(lib_directory,"/TEMPLATE_ill.pt2"))


# *******************************************

#separate header
headerline<-pmatch(":endHeader",template)
header<-template[1:headerline]
data<-template[headerline+1:length(template)]
data<-data[!is.na(data)] #remove NAs


#convert to dataframe
splitfunction<-function(dataline){unlist(strsplit(dataline," +"))}

#initialize numeric and string variable
masternum<-data.frame()
masterstation<-vector()

#loop to split string and parse in variables
for(i in 1:length(data)){
numdata<-as.numeric(splitfunction(data[i])[c(-1,-4)])
station<-toString(splitfunction(data[i])[4])
masternum<-rbind(masternum,numdata)
masterstation<-c(masterstation,station)
}
#combine into dataframe and label columns
data<-cbind(masternum[,c(1,2)],masterstation,masternum[,c(3,4)])
names(data)<-c("long","lat","Station","level","datum")

if(file_extension=="mdb"){
data[1,4]<-LWquery(75,query.date,DBSource)#LOW
data[2,4]<-LWquery(17,query.date,DBSource)#LS
data[3,4]<-LWquery(132,query.date,DBSource)#Rainy Lake
data[6,4]<-LWquery(82,query.date,DBSource)#Slave Falls
data[7,4]<-LWquery(79,query.date,DBSource)#Whitedog
data[10,4]<-LWquery(25,query.date,DBSource)#Manitou Falls
data[12,4]<-LWquery(34,query.date,DBSource)#Caribou Falls
data[13,4]<-LWquery(278,query.date,DBSource)#LSJ
data[17,4]<-LWquery(188,query.date,DBSource)#Namakan
data[18,4]<-LWquery(39,query.date,DBSource)#LLC
}

if(file_extension=="sqlite"){
data[1,4]<-LWquerySQL(75,query.date,DBSource)#LOW
data[2,4]<-LWquerySQL(17,query.date,DBSource)#LS
data[3,4]<-LWquerySQL(132,query.date,DBSource)#Rainy Lake
data[6,4]<-LWquerySQL(82,query.date,DBSource)#Slave Falls
data[7,4]<-LWquerySQL(79,query.date,DBSource)#Whitedog
data[10,4]<-LWquerySQL(25,query.date,DBSource)#Manitou Falls
data[12,4]<-LWquerySQL(34,query.date,DBSource)#Caribou Falls
data[13,4]<-LWquerySQL(278,query.date,DBSource)#LSJ
data[17,4]<-LWquerySQL(188,query.date,DBSource)#Namakan
data[18,4]<-LWquerySQL(39,query.date,DBSource)#LLC
}

Filelink<-paste0(full_output_path,"/",format(as.Date(query.date),"%Y%m%d"),"_ill.pt2")

#Write header to the file
writeLines(header, con = Filelink)

#write table to the file, append=T,row.names=F,col.names=F,sep="\t" (tab deliminated)
write.fwf(data, Filelink, append=TRUE,rownames=FALSE,colnames=FALSE,sep="\t")



