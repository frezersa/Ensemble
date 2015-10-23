#*****************************************
#script to take modelled lake levels from the most recent spin-up and create a .pt2 file for the hindcast and forecast run
#*****************************************

rm(list=ls())


#check and install packages if required
list.of.packages <- c("gdata")
new.packages <- list.of.packages[!(list.of.packages %in% installed.packages()[,"Package"])]
if(length(new.packages)) install.packages(new.packages,repos='http://cran.us.r-project.org')
suppressWarnings(suppressMessages(library(gdata)))

#Get arguments
args <- commandArgs(TRUE)
cat(paste("1 - ",script_directory <- args[1]),"\n") #working directory
cat(paste("2 - ",source_file <- args[2]),"\n")
cat(paste("3 - ",write_file <- args[3]),"\n")
#script_directory<-"C:/Ensemble_Framework/EC_Operational_Framework/Model_Repository/scripts"
#source_file <- "C:/Ensemble_Framework/EC_Operational_Framework/Model_Repository_spinup/wpegr/results/lake_sd.csv"
#write_file <- "C:/Ensemble_Framework/EC_Operational_Framework/Model_Repository/wpegr/level/20140101_ill.pt2"

#get modelled lake levels
tmp<-read.csv(source_file)

#initialize data.frame
jam<-data.frame(lake=seq(1,58,1),elevation=round(as.numeric(tmp[nrow(tmp),seq(2,401,7)]),5)[1:58])
names(jam)<-c("lake","level")

#get lake level template
template<-readLines(paste0(script_directory,"/../lib/TEMPLATE_ill.pt2"))

#separate header
headerline<-pmatch(":endHeader",template)
header<-template[1:headerline]
data<-template[headerline+1:length(template)]
data<-data[!is.na(data)] #remove NAs


#function to convert to dataframe
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
data$level<-jam$level



#Write header to the file
writeLines(header, con = write_file)

#write table to the file, append=T,row.names=F,col.names=F,sep="\t" (tab deliminated)
write.fwf(data, write_file, append=TRUE,rownames=FALSE,colnames=FALSE,sep="\t")

