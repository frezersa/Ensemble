
#
# File IO library (libFileIO.r)
#
# A list of functions used for reading and writing file types for hydrological applications

#load dependant libraries
library (xts)


ReadFlowCsvAsTS <- function(file.name) {
# ReadFlowCsvAsTS
#
# Requires columns named "Date" and "Flow"
# Currently the format needs to be "Y/M/D" in the date column
#
# Args:
#	file.name - string of the file name to be read.

	csv.data <- read.csv(file.name)
	csv.date <-  as.Date(csv.data$Date, format="%Y/%m/%d")
	csv.flow <- csv.data$Flow
	
	flow.ts <- xts(csv.flow, csv.date)
}


ReadUSGSFlowFile <- function(file.name) {
# Read USGS Flow File.
# 
# Function that goes through the USGS standard daily flow text file
# and produces a data.frame with all the contained data for processing
#
	
	#read the tab delimeted file with the comment character set.
	usgs.table <- read.delim(file.name, comment.char="#")
	
	#remove the first line which is a units line
	usgs.table <- usgs.table[-1,]
	
	#calculate datetime and append to data.frame
	usgs.table$Date <- as.Date(usgs.table[,3])
	#usgs.table$Date <- lapply(usgs.table[, 3], as.Date) #runs very slowly!
	#calculate flow in m3/s and append to data.frame
	usgs.table$flow.cfs <- (as.numeric(as.character(usgs.table[,4])))
	usgs.table$flow.cms <- sapply(usgs.table$flow.cfs, function(x) x*(0.3048^3))	
	
	usgs.table	
	
}

WriteUSGSFlowFileCSV <- function(usgs.table, file.name) {
#  WriteUSGSFlowFileCSV
# 
#  Write USGS data into a standard flow CSV file (with "Date" having the date and "Flow" containing the flow in m3/s)

	
	#build the data frame in the appropriate format
	usgs.table.csv <- data.frame(agency_cd=usgs.table$agency_cd, site_no=usgs.table$site_no, Date=usgs.table$Date, Flow=usgs.table$flow.cms)		
	#write the dataframe to the specified file (Excluding the row numbers. 
	write.csv(usgs.table.csv, file.name, row.names=FALSE)	
	usgs.table.csv
}