#***********************************
#Name:LWCBtoTBO
#Written On: October 24, 2013
#Written By: James Bomhof
#Description: Script to export data from the LWCB database to TBO files for WATFLOOD. The
#data is written to TB0 files (one file for each year, 1 line = 1 day)
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
#                "Bear_Pass_RL",131,
#                "Boundary_Falls_WR",257,
#                "Minaki_WR",78,
#                "Pakwash",197,
#                "Campbells_Camp_LLC",39)
# #raingdata
# StationNames=c("Armstrong",543,
#                "Atikokan",588,
#                "Babbit",645,
#                "Bemidji",627,
#                "Cat_River",85,
#                "Cedar_River",92,
#                "Cook",636,
#                "Cyclone",112,
#                "Dryden",94,
#                "Ear_Falls",597,
#                "Ely",642,
#                "Emerson",549,
#                "Flag_Island",300,
#                "Fort_Frances",579,
#                #"Gimli",555,
#                "Goldpines",265,
#                "Great_Falls",561,
#                "Hanson",428,
#                "Indian_Bay",239,
#                "Kabetogama",603,
#                "Kenora",108,
#                "Lac_la_Croix",151,
#                "LS_Post",89,
#                "Orr",606,
#                "Pickle_Lake",86,
#                "Pinawa",585,
#                "Rawson_Lake",95,
#                "Roseau",612,
#                "Sioux_Lkt",87,
#                "Sprague",110,
#                "Squirrel_Island",396,
#                "Thunder_Bay",567,
#                "Upsala",100,
#                "Vermillion_River",153,
#                "Waskish",624,
#                "Winnibig_Lake",319,
#                "Winnipeg",573,
#                "Wolf_Ridge",648)
# #rin data
# StationNames=c("LOW",149,
#                "LS",164,
#                "LSJ",168,
#                "LLC",157,
#                "Namakan_L",172,
#                "Rainy_L",176,
#                "Umfreville",180)
# #strfw data
# StationNames=c("Alban_River",6,
#                "Cat_River",2,
#                "Lac_La_Croix",40,
#                "Basswood_Lake",38,
#                "Turtle_R",56,
#                "Atikikan_R",51,
#                "Pinewood_River",65,
#                "Manitou_Rapids",67,
#                "LOW",76,
#                "Whiteshell",287,
#                "Whitemouth_R",285,
#                "Bird_River",393,
#                "Sioux_Lookout",258,
#                "Umfreville_ER",12,
#                "McDougal_SR",10,
#                "Root_River",5,
#                "Chukuni_R",22,
#                "Troutlake_R",20,
#                "Eagle_River",259,
#                "Quibell",29,
#                "Dryden",261,
#                "Cedar_R",24,
#                "Salveson",33,
#                
#                "Kawishi_River",293,
#                "Vermilion_River",42,
#                "BigFork_River",62,
#                "Rapid_River",510,
#                
#                "Slave_Falls",83,
#                "Ear_Falls",18,
#                "Manitou_Falls",26,
#                "Caribou_Falls",35
#                #"Whitedog",80
#                )
# #tempg data
# StationNames=c("Armstrong",544,545,
#                "Atikokan",589,590,
#                "Babbit",646,647,
#                "Cook",637,638,
#                "Dryden",141,142,
#                "Ear_Falls",598,599,
#                "Ely",643,644,
#                "Flag_Island",299,298,
#                "Fort_Frances",580,581,
#                "Gimli",556,557,
#                "Great_Falls",562,563,
#                "Kabetogama",604,605,
#                "Kenora",137,138,
#                "Pickle_Lake",133,134,
#                "Pinawa",586,587,
#                "Rawson_Lake",320,321,
#                "Red_Lake",135,412,
#                "Seagull",655,656,
#                "Sioux_Lkt",139,409,
#                "Sprague",145,421,
#                "Thief_River",622,623,
#                "Thunder_Bay",568,569,
#                "Upsala",296,297,
#                "Winnipeg",574,575,
#                "Wolf_Ridge",649,650)
#div
#StationNames=c("Root_R",5)

rm(list=ls())

cat("\n Running LWCBtoTB0 Script ********************\n")
# ======= inputs
#
#= command line arguments
# only want arguments after --args
args <- commandArgs(TRUE)

#= variable mappings
# root directory of scripts in ..\writeTB0's
cat(paste("1 - ",script_directory <- args[1]),"\n")
# script_directory <-"C:/WR_WTFLD_Framework_D/Model_Repository/scripts"

# output directory to write tb0's
cat(paste("2 - ",model_directory <- args[2],"\n")) # "D:/Projects/LWCB_Automation/EC_Repo/wpegr"
# model_directory <- "C:/WR_WTFLD_Framework_D/Model_Repository/wpegr"

cat(paste("3 - ",directory_name <- args[3],"\n")) #"diver/level/raing/resrl/strfw/tempg"
# directory_name <- "tempg"

cat(paste("4 - ",Type <-args[4],"\n")) #"diver/level/raing/rin/rel/strfw/tempg"
# Type<-"tempg"
#return error message if type doesn't match predfined values
if(Type!="diver"&Type!="level"&Type!="raing"&Type!="rin"&
     Type!="rel"&Type!="strfw"&Type!="tempg"&Type!="rel"){
  stop("Streamflow type does not match defined values (diver/levels/raing/rin/rel/rout/strfw/tempg)")
}

# year query range
# TODO: these should be date objects
cat(paste("5 - ",start_date <- as.Date(args[5]),"\n")) # 1978
# start_date <- as.Date("2004-01-01")
start_year <- as.numeric(format(start_date,"%Y"))

cat(paste("6 - ",end_date <- as.Date(args[6]),"\n")) # 2013 
# end_date <- as.Date("2005-12-31")
end_year <- as.numeric(format(end_date,"%Y"))

# location of LWCB DB
cat(paste("7 - ",DBSource<- args[7],"\n"))
# DBSource<-"Z:/LWS_Db/lwcb.mdb"
# DBSource<-"C:/Test_FrameWork/EC_Operational_Framework/LWCB_WATFLOOD_DATA.sqlite"


# full path for output file
full_output_path = file.path(model_directory,directory_name)

#Get string of Station Names and Station numbers
StationNames<- unlist(strsplit(args[8],","))
# StationNames=c("Armstrong",544,545,
#                "Atikokan",589,590,
#                "Babbit",646,647,
#                "Cook",637,638,
#                "Dryden",141,142,
#                "Ear_Falls",598,599,
#                "Ely",643,644,
#                "Flag_Island",299,298,
#                "Fort_Frances",580,581,
#                "Gimli",556,557,
#                "Great_Falls",562,563,
#                "Kabetogama",604,605,
#                "Kenora",137,138,
#                "Pickle_Lake",133,134,
#                "Pinawa",586,587,
#                "Rawson_Lake",320,321,
#                "Red_Lake",135,412,
#                "Seagull",655,656,
#                "Sioux_Lkt",139,409,
#                "Sprague",145,421,
#                "Thief_River",622,623,
#                "Thunder_Bay",568,569,
#                "Upsala",296,297,
#                "Winnipeg",574,575,
#                "Wolf_Ridge",649,650)
# StationNames<- unlist(strsplit("LOW_rel,76,05QE006,18,05PC019,58,05PF069,9004,05PF068,9005,05PF063,9006,05PE010,9007,05QD016,9008,05QD003,9009,05QE007,9010,Trout_L,9011,05QE005,9012,L_St_Jos,9013,05PB009,9014,Atikoka,9015,Des_Mil,9016,Namakan,44,05PA006,9018,Basswoo,9019,Saganag,9020,Gull_Ro,9021,L_Vermi,9022,Nungess,9023,L_of_Ba,9024,Sturgeo,9025,Miniss_,9026,Savani_,9027,Bamaji_,9028,Kezik_L,9029,Fawcett,9030,Cat_Lake,9031,Birch_L,9032,Kabetog,9033,Vermill,9034,No_name,9035,Orr_Lake,9036,No_name,9037,Wabaska,9038,Sydney_,9039,Wh_Otte,9040,Bird_L,9041,Roger_F,9042,Press_L,9043,Barrel_,9044,Indian_,9045,Sapawa_,9046,Crooked,9047,Coulsen,9048,Brereto,9049,Winton_,9050,Gauge45,9051,Wegg_Lake,9052,Wilcox_,9053,Oak_Lake,9054,Lount_Lake,9055,Separat,9056,Packwash,9057",","))
#StationNames<- unlist(strsplit("",","))

cat(paste("9 - ",Nudge<- args[9],"\n"))

#= import libraries
# set working directory to scripts root directory. permits relative path.
setwd(script_directory)
source("rlib/LWSlib.R")


# *******************************************

#Set header defaults for different file types (tmp, strfw, levels, etc.)
#Set Defaults
file_extension<-file_ext(DBSource)
ColumnLocationX1<-NULL
ColumnLocationY1<-NULL
UnitConversion<-NULL
AttributeUnits<-NULL
RoutingDeltaT<-NULL
Elevation<-NULL
Value1<-NULL
coeff1<-NULL
coeff2<-NULL
coeff3<-NULL
coeff4<-NULL
coeff5<-NULL
smooth<-1#used in rollmean function to smooth values if necessary
Deltatime <- "24"

#Set headers specific to 'diver'
if(Type=="diver"){
  ColumnUnits<-"m3/s"
  Name<-"diversion(s)"
  tag<-"div"
  AttributeUnits<-1
  Value1<-1
  ColumnLocationX<-(-91.35)
  ColumnLocationY<-50.967
  ColumnLocationX1<-(-91.4580)
  ColumnLocationY1<-50.8690
  NullValue<-(-1)
}

#Set headers specific to 'level'
if(Type=="level"){
  ColumnUnits<-"masl"
  Name<-"Observed_lake_levels"
  tag<-"lvl"
  coeff1<-0
  coeff2<-0
  coeff3<-0
  coeff4<-0
  coeff5<-0
  smooth<-3 
  NullValue<-(-1)
}

#Set headers specific to 'raing'
if(Type=="raing"){
  ColumnUnits<-"mm"
  Name<-"daily_precip"
  tag<-"rag"
  Elevation<-1#any value other than "NULL" will trigger Elevations to be output
  UnitConversion<-1
  NullValue<-(-99.99)
}

#Set headers specific to 'rin'
if(Type=="rin"){
  ColumnUnits<-"m3/s"
  Name<-"lakeInflows"
  tag<-"rin"
  Value1<-1
  NullValue<-(-1)
  smooth<-1 
}

#Set headers specific to 'rel'
if(Type=="rel"){
  ColumnUnits<-"m3/s"
  Name<-"ReservoirReleases"
  tag<-"rel"
  NullValue<-(-1)
  
  #get coefficients from template
  dummy<-readLines("../lib/TEMPLATE_rel.tb0",warn=F)
  
  #get station names
  linenumber.name <- grep(pattern = ":ColumnName", ignore.case=T, dummy)
  tmp<-unlist(dummy[linenumber.name])
  Names<-scan(text=tmp, what='character', quiet=TRUE)[-1]
  
  #get and set coefficients
  linenumber.coef <- grep(pattern = ":coeff", ignore.case=T, dummy)[1]
  for(i in 0:4){
    tmp<-unlist(dummy[linenumber.coef+i])
    assign(paste0("coeff",(i+1)),as.numeric(scan(text=tmp, what='character', quiet=TRUE)[-1]))
  }
}

#Set headers specific to 'strfw'
if(Type=="strfw"){
  ColumnUnits<-"m3/s"
  Name<-"streamflow"
  tag<-"str"
  AttributeUnits<-1
  RoutingDeltaT<-1
  coeff1<-0
  coeff2<-0
  coeff3<-0
  coeff4<-0
  Value1<-1
  if(Nudge=="True"){Value1<-2}
  NullValue<-(-1)
}

#Set headers specific to 'tempg'
if(directory_name=="tempg"){
  ColumnUnits<-"dC"
  Name<-"temperatures"
  tag<-"tag"
  Elevation<-1#any value other than "NULL" will trigger Elevations to be output
  UnitConversion<-0
  NullValue<-(-99.99)
  Deltatime <- "12"
}      



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
  
  #change the coefficients to 0 if reservoir release data exists
  if(Type=="rel"){
    coeff1[MasterList$Level<9000]<-0
    coeff2[MasterList$Level<9000]<-0
    coeff3[MasterList$Level<9000]<-0
    coeff4[MasterList$Level<9000]<-0
    coeff5[MasterList$Level<9000]<-0
  }
}

#Add locations to MasterList
if(file_extension=="mdb"){MasterList<-cbind(MasterList,t(sapply(MasterList[,2],locationquery,DBSource=DBSource)[2:4,]))}
if(file_extension=="sqlite"){MasterList<-cbind(MasterList,t(sapply(MasterList[,2],locationquery,DBSource=DBSource,useSQL=TRUE)[2:4,]))}

#Initialize multicolumn xts object
AllStations<-xts()
i=3
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

#Define Begining Year
Years<-seq(start_year,end_year,1)

#create directory to store tb0s
dir.create(full_output_path,showWarnings=FALSE)

#Write tb0 for each year
for(i in 1:length(Years)){
  
  #subset object by year
  subData<-AllStations[toString(Years[i])]
  #substitute Nullvalue for NA values (default for WATFLOOD)
  subData[is.na(subData)]<- NullValue
  
  #start at the begining date, else start at Jan 1
  if(i==1){StartDate<-format(start_date,"%Y/%m/%d")
                             StartDateTitle<-format(start_date,"%Y%m%d")}else{
                               StartDate<-paste0(Years[i],"/01/01")
                               StartDateTitle<-paste0(Years[i],"0101")}

  #Write TB0 for specific year
  suppressWarnings(writeTB0(Data=as.data.frame(subData),
           
           Projection="LATLONG",Ellipsoid="WGS84",
           StartDate,StartTime="00:00:00.0",
           Deltatime=Deltatime,ColumnType="float", Author="LWCB",
           
           ColumnNames=MasterList$StationNames,
           if(Type!="diver"){ColumnLocationX=MasterList$Longitude}else{ColumnLocationX=ColumnLocationX},
           if(Type!="diver"){ColumnLocationY=MasterList$Latitude}else{ColumnLocationY=ColumnLocationY},
           if(is.null(Elevation)){Elevation=Elevation}else{Elevation<-MasterList$Elevation},
           Name=Name,ColumnUnits=ColumnUnits,
           
           ColumnLocationX1=ColumnLocationX1,ColumnLocationY1=ColumnLocationY1,
           UnitConversion=UnitConversion,AttributeUnits=AttributeUnits,
           RoutingDeltaT=RoutingDeltaT,
           
          Value1=Value1,
           coeff1=coeff1,coeff2=coeff2,coeff3=coeff3,coeff4=coeff4,coeff5=coeff5,
           FileName=paste(full_output_path,"/",StartDateTitle,"_",tag,sep="")))
           
           
}

