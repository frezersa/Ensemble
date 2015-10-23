#**********************************
#Script to modify an r2c file
#This is used to adjust precip and temperature hindcast files so that modelled = observed at t=0
#This is a manual form of Nick's precipitation adjustment factor mentioned in the WATFLOOD manual
#************************************

#initialize and get libraries
rm(list=ls())


#check and install packages if required
list.of.packages <- c("raster","rgdal")
new.packages <- list.of.packages[!(list.of.packages %in% installed.packages()[,"Package"])]
if(length(new.packages)) install.packages(new.packages,repos='http://cran.us.r-project.org')

suppressWarnings(suppressMessages(library(raster)))
suppressWarnings(suppressMessages(library(rgdal)))


#Get arguments
args <- commandArgs(TRUE)
cat(paste("1 - ",script_directory <- args[1]),"\n") #working directory
cat(paste("2 - ",r2c.pathname <- args[2]),"\n") #name of r2c file
cat(paste("3 - ",param.locat <- args[3]),"\n") #location of parameter file
cat(paste("3 - ",adjustment <- args[4]),"\n") #addition or multiplication

# script_directory<-"C:/Test_Framework/EC_Operational_Framework/Model_Repository/scripts"
# r2c.pathname<-"C:/Test_Framework/EC_Operational_Framework/Model_Repository/wpegr/tempr/20150101_tem.r2c"
# param.locat<-"..\\lib\\TempAdjust.csv"
# adjustment<-"tempadd"

# r2c.pathname<-"C:/Test_Framework/EC_Operational_Framework/Model_Repository/wpegr/radcl/20150101_met.r2c"
# param.locat<-"..\\lib\\PrecipAdjust.csv"
# adjustment<-"precipmult"

#set working directory
setwd(script_directory)
source("rlib/LWSlib.R")

r2c.name<-basename(r2c.pathname)
r2c.path<-dirname(r2c.pathname)

if(adjustment=="add"){decimal<-1;frametime<-"hours"}else{decimal<-3;frametime<-"days"}

#if an 'orginal' copy doesn't exist then create copy
 if(!file.exists(paste0(r2c.path,"/","Orig_",r2c.name))){
   file.copy(r2c.pathname,paste0(r2c.path,"/","Orig_",r2c.name))
   } 


#get and parse parameter file
stationweights<-read.csv(param.locat)
weightdates<-c(as.Date(strptime(names(stationweights)[-c(1,2)],"X%Y.%m.%d")),Sys.Date())



#Check to see if there is data in the paramter file, only execute adjust function if adjustments need to be made
if(length(weightdates)!=2){
  cat("Reading r2c file...\n")

  #load the 'original' file
  r2c.file<-readr2c(paste0(r2c.path,"/","Orig_",r2c.name))
  
  #get dates from r2c file
  precipdates<-as.Date(strptime(names(r2c.file[[2]]),"X%Y.%m.%d.%H.%M"))
  
  
  #get boundary shapefile
  boundary <- readOGR(dsn=paste0(script_directory,"/../lib/shapefiles"),layer="Watershed_SubBasins",verbose=F)
  # boundary@data$Basin
  
  #find which cells are in each basin
  cellinbasin<-cellFromPolygon(r2c.file[[2]],boundary,weights=F)
  
  
  #make adjustments (currently only multiply by factor)
  cat("Applying adjustments...\n")
  j=1
  
  for(j in 1:(length(weightdates)-1)){
  
    precip.sub<-subset(r2c.file[[2]],c(1:length(precipdates))[precipdates>=weightdates[j]&precipdates<weightdates[j+1]])
    weight<-stationweights[,j+2]
  
  
    if(adjustment=="tempadd"){
      for(i in 1:9){
        precip.sub[cellinbasin[[i]]]<-precip.sub[cellinbasin[[i]]]+weight[i]
        }
      } 
    
    
    if(adjustment=="precipadd") {
      for(i in 1:9){
        precip.sub[cellinbasin[[i]]]<-precip.sub[cellinbasin[[i]]]+weight[i]
        #precip.sub[cellinbasin[[i]]]<0){precip.sub[cellinbasin[[i]]]<-0 
        }
    }
    
    
    if(adjustment=="precipmult") {
      for(i in 1:9){
        precip.sub[cellinbasin[[i]]]<-precip.sub[cellinbasin[[i]]]*weight[i]
        }
    }
    
  
    
    if(j==1){r2c.new<-precip.sub}else{r2c.new<-stack(r2c.new,precip.sub)}
  }
  
  #plot(sum(r2c.new))
  
  #replace the original file with the adjusted file
  cat("Writing adjusted r2c file...\n")
  writer2c(header=r2c.file[[1]],data=r2c.new,FileName=r2c.pathname,decimal=decimal,frametime=frametime)
  
}else{
  cat("Parameter file contains no adjustment; no changes made to r2c file \n\n")
}