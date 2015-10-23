# libMaps.R
#
# a library of map-related functions and variables to simplify the 
# geospatial representation of data *quickly* 



#Key Projection strings for use in "sp" package


library(sp)             # classes for spatial data
library(raster)
library(rasterVis)      # raster visualisation
library(maps)
library(maptools)
library(mapproj)
library(RColorBrewer)
library(rgdal)

#LAT LONG
proj.latlong <- CRS("+proj=longlat")

#Canadian Albers Equal Area
proj.albers<- CRS("+proj=aea   
                  +lat_1=50.0
                  +lat_2=70.0
                  +lat_0=40.0 
                  +lon_0=-96.0
                  +x_0=0.0
                  +y_0=0.0")
				  
#Canadian Albers Equal Area
proj.albers.USGS<- CRS("+proj=aea   
                  +lat_1=29.5
                  +lat_2=45.5
                  +lat_0=23.0 
                  +lon_0=-96.0
                  +x_0=0.0
                  +y_0=0.0")

#Northern Polar Stereo
proj.polarstereo.N <- CRS("+proj=stere 
                          +lat_ts=90
                          +lat_0=90
                          +lon_0=0.0
                          +k_0=1.0
                          +x_0=0.0
                          +y_0=0.0")


#Some of these functions are simple wrappers so that we don't have to remember them or how they work.

WorldMap <- function(){
  #this will eventually expand with options from different data sources when found.
  x<-getData('countries')
    
}

CanadaMap <- function(provinces=T){

  #this will eventually expand with options from different data sources, etc. when found.
  
  if(provinces){
    lvl<-1
  }else{
    lvl<-0
  }
  
  x<-getData('GADM', country="CAN", level=lvl)
  
}

USAMap <- function(states=T){
  
  #this will eventually expand with options from different data sources, etc. when found.
  
  if(states){
    lvl<-1
  }else{
    lvl<-0
  }
  
  x<-getData('GADM', country="USA", level=lvl)
  
  
}

CanadaMapAltitude <- function(mask=T){

  x<-getData('alt', country='CAN', mask=mask)

}