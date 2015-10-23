#
# Hydrograph Processing/Generation Library (libHydro.r)
#
# 	A list of functions that have been collected to assist in developing design hydrograps  
#	Includes developing balanced hydrographs, identifying hydrogrphs from time series etc.

source("rlib\\libHydroStats.r")
library(xts)

BhScaleHydroFlow <- function(ts, max.SF, time.SF, peak, exc_res){
	max.flow<- max(ts)
	ts.SF <- BhScaleFactorHyp(ts, max.flow, max.SF)
	event_scaled <- ts* ts.SF
	event_scaled <-BhScaleHydroTime(event_scaled, time.SF)
	event_scaled <-event_scaled*(peak/max(event_scaled))
	event_scaled
}

#scale the times by the scale factor
BhScaleHydroTime<- function(ts, time.SF){
	days <- (0:(length(ts)-1))*time.SF
	days.scaled <- seq(0,tail(days,1), 1)
	event_scaled <- approx(days, ts, xout=days.scaled)$y
	event_scaled
}

# adjust the scale factor with a hyperbolic function from 1 (no change) at the max flow to the maximum scale factor at zero flow
BhScaleFactorHyp <- function(ts, max.flow, max.SF) {
	b <- max.flow/(max.SF-1) # decay rate fixed to set ratio to 1 at max flow
	ts.SF.hyp <-  max.SF / (1+ ts/b)
	ts.SF.hyp
}

#find the root mean squared error of the QdF
BhError <- function(ts, max.SF, time.SF, peak, exc_res, daily.vals){
	event_scaled <- BhScaleHydroFlow(ts, max.SF, time.SF, peak, exc_res)
	
	if(length(event_scaled) >= 31){
		qdf <- QdfEvent(event_scaled, daily.vals)
		error <- RMSE(exc_res[exc_res>c(exc_res[-1],0)], qdf[exc_res>c(exc_res[-1],0)])
	}else{
		error <- 999999
	}
	#print(peak)
	#print(error)
	error
}

BalancedHydrograph <- function(orig.event, QdF, daily.vals) {
#
# BalancedHydrograph
#
# Desc: takes an input hydrograph and scales it to match the QdF vector supplied
#
# Args: orig.hydrograph - an XTS hydrograph (?) in daily flows.
#		QdF - a qdf matrix
#		daily.vals - the array of daily values (same dimensions as QdF)
	
	
	# initial scaling of the hydrograph to the 1-day maximum flow.
	event.scaled <- orig.event*(QdF[1]/max(orig.event)) 
  
  summary(event.scaled)
		
	# dialate the event to account for missing dates at trailing end
	if(length(event.scaled) < 31){
		event.scaled <- BhScaleHydroTime(event.scaled, 31/(length(orig.event)-1)) #initial time scaling
	}
	
	#optimize the hydrograph fit.
	if(QdF[1] >= max(QdF[-1])){ #fit the 1day excatly if it is the highest of the QdF values
		param <- c(1, 1)
		
		#optimize the fit of the hydrograph
		optim.result<-optim(param, function(x){BhError(event.scaled, x[1], x[2],QdF[1], QdF, daily.vals)}, method="L-BFGS-B", lower=c(0.01,1), control=list(maxit=1000000, parscale=c(5,1)))
		param<-c(optim.result$par, QdF[1])
	}
	
	else{ # optimize the 1day if it is not the maximum value.
		param <- c(1, 1, max(event.scaled))
		optim.result<-optim(param, function(x){BhError(event.scaled, x[1], x[2], x[3], QdF, daily.vals)}, method="L-BFGS-B", lower=c(0.01,1,0.01), control=list(maxit=1000000, parscale=c(5,1,10)))
		param<-optim.result$par
	}
	
	#apply the optimized parameters to the event.scaled value.
	event.scaled <- BhScaleHydroFlow(event.scaled, param[1], param[2], param[3], QdF)
	
	event.scaled
	
}

HydroSpaghetti <- function(flow.ts, plot.chart=FALSE, plot.title=NULL){
# HydroSpaghetti
#
# Function that takes a time series and plots a "spaghetti" plot of all the annual hydrographs
# and also plots a median and quartile lines -- illustrated to visually represent the flow patterns
# for that station.
#
	#maximum flow (for plotting0 
	max.flow <- max(flow.ts, na.rm=TRUE)

  print(max.flow)
  
	# Extract date index
	time.index <- index(flow.ts)

	# fill in the missing dates with NA values
	#flow.ts <- TsFillMissingDates(flow.ts)
	
	# determine the list of years
	years <- format(as.numeric(format(time.index, "%Y")))
	years <- unique(years)
	
	#remove first year and last year (we need a sequence that is complete for every calendar year)
	years <- years[-1]
	years <- years[-length(years)]

	first <- TRUE
	for (i in years){
				
		if(first){ # first step through the loop
		
      
      y.lim <- c(0,max.flow)
      x.lim <- c(0,366)
      #x.lim <- c(0,60)
			# set up plotxlim=c(0,366)
			plot(coredata(flow.ts[i]), type="l", col="grey85", main=plot.title, xlab="Julian Day", ylab="Snow on Ground - cm", ylim=y.lim, xlim=x.lim)	
			
			# track data in a matrix 
			c.data.temp <- coredata(flow.ts[i])
			flow.matrix <- c.data.temp[1:365]
			
		} else {
			lines(coredata(flow.ts[i]), col="grey85")
			c.data.temp <- coredata(flow.ts[i])
			flow.matrix <- cbind(flow.matrix, c.data.temp[1:365])
		}
		
		first <- FALSE
	}

	flow.median <- apply(flow.matrix, 1, median, na.rm=T)
	flow.25 <- apply(flow.matrix, 1, function(x) quantile(x,0.25, na.rm=T))
	flow.75 <- apply(flow.matrix, 1, function(x) quantile(x,0.75, na.rm=T))
  flow.max <- apply(flow.matrix, 1, function(x) max(x, na.rm=T))
	flow.min <- apply(flow.matrix, 1, function(x) min(x, na.rm=T))
  
	lines(flow.median, col="red", lwd=2)
	lines(flow.25, col="red", lwd=1, lty=2)
	lines(flow.75, col="red", lwd=1, lty=2)
  
  
   flow.stats <- cbind(flow.median, flow.25, flow.75, flow.max, flow.min)
  
	out.list <- list(flow.matrix=flow.matrix, flow.stats=flow.stats)

}

TsFillMissingDates <- function (flow.ts, interval="day") {
#
# TsFillMissingDates
#
# Function that takes a regular time-series (i.e. daily data), and fills the missing dates
# with NA values (so that every day in the period is accounted for whether there is data or not)

	#fill in missing daily data in flow.ts with null values
	min.index <- min(time.index)
	max.index <- max(time.index)
	time.index.full <- seq.Date(min.index, max.index, by=interval)
	flow.ts.full <- xts(rep(NA, length(time.index.full)), time.index.full)
	flow.ts.merge <- merge.xts(flow.ts.full, flow.ts, join="left")
	flow.ts <- flow.ts.merge[,2]

}


EventRemoveBaseflow <- function(ts, inflec.index=NULL, type=4){
#
# EventRemoveBaseflow
#
# Function to remove the baseflow from the timeseries event using one of 4 methods
# 	
#
	if(type == 1){ #method 1: baseflow is a horizontal line from the starting point
		ts <- ts[ts>=as.double(ts[1])]-as.double(ts[1])
	}
	else if(type == 2){ #method 2: baseflow is a straight line from start point to endpoint
		line = approx(c(1,length(ts)), c(coredata(ts[1]),tail(coredata(ts),1)), n = length(ts)) # the baseflow line
		ts <- ts-line$y
	}
	else if(type == 3){ #method 3: baseflow is a straight line from the starting point to the inflection point
		if(length(inflec.index)>0){ # check if an inflection point was found
			line = approx(c(1,inflec.index), c(coredata(ts[1]),coredata(ts[inflec.index])), n = inflec.index) #the baseflow line
			ts <- ts[1:inflec.index]-line$y
		}else{
			ts <- rep(0,length(ts))
		}
	}
	#method 4: dont remove baseflow
	ts # the new time series
}


HydrographVolume <- function(ts, inflec.index){
  #  HydrographVolume
  #
  #  Returns the volume of the hydrograph after 4 methods of handling baseflow (4 element array)
  #  The methods include: 
  #   1 - baseflow horizontal from the starting point
  #   2 - baseflow as line (not horizontal) from starting point to end point
  #   3 - baseflow is from the starting point to the identified inflection point
  #   4 - no removal of baseflow in volume calculation
  #   
  #  Args: ts - a hydrograph time series
  #        inflec.index - a list of indices to mark hydrogrpah inflection points for volume calculations (method 3)

  #Method 1
  vol1 = sum(coredata(ts[ts>=ts[1]])-coredata(ts[1]))*86400 #horizontal line from start point
  
  #Method 2
  if(length(ts)>1){
    line <- approx(c(1,length(ts)), c(coredata(ts[1]),tail(coredata(ts),1)), n = length(ts)) #line to endpoint
    vol2 <- (sum(coredata(ts))-sum(line$y))*86400
  }else{
    vol2=0
  }
  
  #Method 3
  if(length(inflec.index)>0 && inflec.index!=1){
    line <- approx(c(1,inflec.index), c(coredata(ts[1]),coredata(ts[inflec.index])), n = inflec.index) #line to inflection point (MACD)
    vol3 <- (sum(coredata(ts[1:inflec.index]))-sum(line$y))*86400
  }else{
    vol3 <- 0
  }
  
  #Method 4 
  vol4 <- sum(coredata(ts))*86400 # don't remove baseflow
  
  #Return Results
  c(vol1,vol2,vol3,vol4)
  
}

HydrographEventMet <- function(ts.event, ts.met){
  # HydrographEventMet
  #
  # Function that takes determines the meteorological stats during an event (max,min,median,mean,sum).  Designed to help identify
  # what sort of precipitation and temperature fluctuations exist during an event to identify it as snomelt, 
  # rain-on-snow, or similar.
  #
  # Args: 
  #   ts.event - hydrograph event timeseries (the min and max dates will be used to calculate the climate stats)
  #   ts.met - meterological time series (can be precip, temperature, or whatever else)
  #
  # Output:
  #   vector including max, min, median, mean, and sum of values
  
  #Establish Rainge
  range = paste(as.Date(.indexDate(ts[1])),"/", as.Date(.indexDate(tail(ts,1))), sep="")
    
  #Perform Calcs
  if(length(ts.met[range][!is.na(ts.met[range])])>0){
    max <- max(ts.met[range], na.rm=T)
    min <- min(ts.met[range], na.rm=T)
    median <- median(ts.met[range], na.rm=T)
    mean <- mean(ts.met[range], na.rm=T)
    sum <- sum(ts.met[range], na.rm=T) 
  } else {
    max <- NA
    min <- NA
    median <- NA
    mean <- NA
    sum <- NA
  }
    
  
  #return results
  results <- c(max, min, median, mean, sum)
  
}