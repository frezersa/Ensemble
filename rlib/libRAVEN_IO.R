# Functions for reading RAVEN File Types

RvReadRVH<- function(file.name){
  # RvReadRVH
  # Function to read the raven RVH file and export a collection (list) 
  
  # wasteful procedure to read ALL lines to extract the header.
  lines <- readLines(file.name)
  lines <- Trim(lines)
  lines.count <- length(lines)
  
  
  
  #Collect HRUs  
  hru.list <- RvReadBlock(":HRUs", ":EndHRUs", file.name)

  #Collect Sub Basins
  sub.basin.list <- RvReadBlock(":SubBasins", ":EndSubBasins", file.name)  
  
  #Basin Initial Conditions
  initial.conditions.list <- RvReadBlock(":BasinInitialConditions", ":EndBasinInitialConditions", file.name)
    
  #Assemble object lists and put into one output list.
  out.list <- list(HRUs=hru.list, SubBasins=sub.basin.list, InitialConditions=initial.conditions.list)
  
}

RvReadRVI<- function(file.name){
  
  # wasteful procedure to read ALL lines to extract the header.
  lines <- readLines(file.name)
  lines <- Trim(lines)
  lines.count <- length(lines)
  
  
  #Soil Parameter Lists
  start.line <- grep(pattern = ":SoilParameterList", lines)
  end.line <- grep(pattern = ":EndSoilParameterList", lines)
  
  
}

RvReadBlock<- function(start.key, end.key, file.name){
  
  # wasteful procedure to read ALL lines to extract the header.
  lines <- readLines(file.name)
  lines <- Trim(lines)
  lines.count <- length(lines)
  
  #Soil Parameter Lists
  start.line <- grep(pattern = start.key, lines)
  end.line <- grep(pattern = end.key, lines)
  
  trim.lines <- lines[(start.line+1):(end.line-1)]
  keyword.lines <- grep(pattern = "^:", trim.lines)
  keywords <- ParseHeaderLines(trim.lines[keyword.lines])
  data.lines <- trim.lines[-keyword.lines]
  data.lines <- gsub(",", " ", data.lines)
  
  #not straight forward to turn a series of lines into a datatable (that I can find).
  #easier if we specify the start and end lines of the file and pull the table in that way.
  skip.lines <- start.line + length(keyword.lines) 
  num.rows <- length(data.lines)
  data.table <- read.table(file.name, header=F, skip=skip.lines, sep=",", nrows=num.rows)
  col.names <- unlist(strsplit(paste(keywords$Attributes), " +"))
  col.units <- unlist(strsplit(paste(keywords$Units), " +"))
  colnames(data.table) <- col.names
  
  block.list <- list(keywords=keywords, data.table=data.table, column.names=col.names, column.units=col.units)
  
}

RvTsShift <- function(ts){
  #function to shift a time-series one index - to correct RAVEN reporting data
  # to more closely match other models and measured data.
  
  flow.index <- index(ts)
  flow.data <- coredata(ts)
  flow.data <- c(flow.data[-1], 0) #add a zero at the end (NAs could break the stats)    
  ts.shifted <- xts(flow.data, flow.index)
  
}

RvMbPlot <- function(wb.tb0.filename, png.title){
  #RvMbPlot
  
  # Plots the mass balance timeseries on a number of plot sheets
  
  file.name <- wb.tb0.filename
  png.filename <- png.title
  wat.bal.tb0 <- ReadTB0(file.name)
  wb.data <- wat.bal.tb0$data.table
  col.count <- dim(wb.data)[2]
  
  #set number of plots per sheet (3x4)
  pps <- 12
  
  #number of plot sheets
  plot.count <- ceiling((col.count-1)/pps) #12 plots per sheet
  
  for(p in 1:plot.count){
    
    temp.filename<- paste(png.filename, ".", p, ".png", sep="")
    
    png(temp.filename, width=1600, height=1200, pointsize=16)
    par( mfrow = c( 3, 4 ) )
    
    start.index <- (p-1)*pps+2
    end.index <- min(start.index+pps-1, col.count)
    
    for (i in start.index:end.index){
      
      title<- colnames(wb.data)[i]    
      ts <- xts(wb.data[,i], wb.data[,1])    
      plot(ts,main=title)
      
    }
    
    dev.off()
    
  }
  
}