#############################
#
# 	libHydroStats.R
# 
#############################
#
#	library used to define the various functions used to evaluate model performance
#
#	Nash Sutcliffe (Daily)
#	Annual Flow Volume R2
#	Annual Flow Volume Bias
#	Monthly Flow Volume Bias 
#	Mean Absolute Error (MAE) for SWE data
#
#############################
#
#	Plotting Functions
#
#	For some functions there is a sister function with the appendix ".Plot"
#	these functions are wrappers of the parent function that generate graphical output
# 	in a standard way
#
#############################


#check and install packages if required
list.of.packages <- c("ggplot2","scales")
new.packages <- list.of.packages[!(list.of.packages %in% installed.packages()[,"Package"])]
if(length(new.packages)) install.packages(new.packages,repos='http://cran.us.r-project.org')

suppressWarnings(suppressMessages(library(ggplot2)))
suppressWarnings(suppressMessages(library(scales)))

 NASH <- function(flow.ts.obs, flow.ts.est, xts.subset=NA, exclude.na=F) {
# NASH - function to calculate the nash sutcliffe coefficient from two time-series datasets
#
#	Args: 	flow.ts.obs - observed flow, an XTS time series with dates and flow values 
#			    flow.ts.est - estimated flow, an XTS time series with dates and flow values
#         exclude.na - an option to force calculation of NASH even if NA values are present
#	Output: single value of the NS coefficient

  #remove observations/estimations that don't have corresponding values in other TS
  if (exclude.na){
    flow.ts.est[is.na(flow.ts.obs)]=NA
    flow.ts.obs[is.na(flow.ts.est)]=NA    
  }
   
  #denominator of NS  
  Qd <- mean(flow.ts.obs, na.rm=exclude.na)
  Qd <- (flow.ts.obs - Qd)^2
  Qd <- sum(Qd, na.rm=exclude.na)     
	
	#numerator of NS  
	Qn <- (flow.ts.obs - flow.ts.est)^2
  Qn <- sum(Qn, na.rm=exclude.na)
		
	#calculate NS value
	NS <- 1 - Qn/Qd

 }
 
 NASH.AnnPlot <- function(flow.ts.obs, flow.ts.est){
 
 	#shift from water year to calendar year
	flow.ts.obs <- WY2CY(flow.ts.obs)
    flow.ts.est <- WY2CY(flow.ts.est) 
  
	# NOT SO STRAIGHTFORWARD AS THE APPLY.YEARLY CAN TAKE ONLY *ONE* TS.
	# May have to loop through the years to calculate?
	#nash.yr <- apply.yearly(rainfall.ts.cs, max)
	
 
 }

 MAE <- function(flow.ts.obs, flow.ts.est, exclude.na=F){
   # returns mean absolute error
    
  #remove observations/estimations that don't have corresponding values in other TS
  if (exclude.na){
    flow.ts.est[is.na(flow.ts.obs)]=NA
    flow.ts.obs[is.na(flow.ts.est)]=NA    
  }

  stat <- flow.ts.obs - flow.ts.est
  stat <- abs(stat)
  stat <- mean(stat, na.rm=exclude.na)  
   
  return(stat)
   
 }
 
  
 MARE <- function(flow.ts.obs,flow.ts.est, exclude.na=T) {
   # returns mean absolute relative error

   #remove observations/estimations that don't have corresponding values in other TS
   if (exclude.na){
     flow.ts.est[is.na(flow.ts.obs)]=NA
     flow.ts.obs[is.na(flow.ts.est)]=NA    
   }
   
  stat <- mean( abs(flow.ts.obs - flow.ts.est) / flow.ts.obs, na.rm=exclude.na)
  return(stat)
 }

 HydrographPlot <- function(flow.ts.obs, flow.ts.est){
	
	x.lab <- ""
	y.lab <- "Flow (cms)"
	title.lab <- "Simulation Hydrographs"
	
	plot(flow.ts.obs, xlab=x.lab, ylab=y.lab, main=title.lab)
	lines(flow.ts.est, col="red")
	
	legend(
		"topleft", 
		c("observed", "estimated"), 
		lty=c(1,1),		
		col=c("black","red"), 	
	)	

 }
 
  HydrographPlotGG <- function(flow.ts.obs, flow.ts.est){
	
	x.lab <- ""
	y.lab <- "Flow (cms)"
	title.lab <- "Simulation Hydrographs"
	
	df.o <- data.frame(date.time=index(flow.ts.obs), flow.obs=coredata(flow.ts.obs))
	df.e <- data.frame(date.time=index(flow.ts.est), flow.est=coredata(flow.ts.est))
	df.mix <- merge(df.o, df.e, by='date.time')
		
	hydro.plot <- ggplot(df.mix, aes(date.time)) + geom_line(aes(y = flow.obs, colour="Observed")) + geom_line(aes(y = flow.est, colour="Estimated"))
	
	# Set colours and remove legend title
	hydro.plot <- hydro.plot + scale_color_manual(values=c("black", "red"), name="") + xlab("Date") + ylab("Flow")
	
 }


AnnualFlowProfile <- function(flow.ts){
  # HydroSpaghetti
  #
  # Function that takes a time series and plots a "spaghetti" plot of all the annual hydrographs
  # and also plots a median and quartile lines -- illustrated to visually represent the flow patterns
  # for that station.
  #
  #maximum flow (for plotting0 
  
  # Extract date index
  
  time.index <- index(flow.ts)
  years <- format(as.numeric(format(time.index, "%Y")))
  years <- unique(years)  
  years <- years[-1]
  years <- years[-length(years)]
  
  first <- TRUE
  
  for (i in years){
    
    if(first){ # first step through the loop            
      c.data.temp <- coredata(flow.ts[i])
      flow.matrix <- c.data.temp[1:365]
      
    } else {
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
  
  flow.stats <- cbind(flow.median, flow.25, flow.75, flow.max, flow.min)
  
  out.list <- list(flow.matrix=flow.matrix, flow.stats=flow.stats)
  
}

AnnualHydrographComparePlotGG <- function(flow.ts.obs, flow.ts.est){
  
  
  
  
  flow.data.obs <- AnnualFlowProfile(flow.ts.obs)
  flow.data.est <- AnnualFlowProfile(flow.ts.est)
  
  dates <- seq(as.Date("2001-01-01"), as.Date("2001-12-31"), by="day")
  fd.1 <- as.data.frame(flow.data.obs$flow.stats)
  fd.1 <- cbind(dates, fd.1, Class="Observed")
  fd.2 <- as.data.frame(flow.data.est$flow.stats)
  fd.2 <- cbind(dates, fd.2, Class="Estimated")
  
  fd <- rbind(fd.1, fd.2)
  
  
  p <- ggplot(data=fd) + 
    scale_color_manual(values=c("red", "blue")) +
    scale_fill_manual(values=c("red", "blue")) +
    geom_line(aes(x=dates, y=flow.median, color=Class) ) +
    geom_ribbon(aes(x=dates, ymin=flow.25, ymax=flow.75, fill=Class), alpha=0.25) + 
    scale_x_date(name="", breaks = "1 month", labels=date_format("%b")) +
    scale_y_continuous(name="Flow (m3/s)")
  
 }
 
 HydrographScatterPlot <- function(flow.ts.obs, flow.ts.est){
	
   # force equal start and end times.
   est.min.index <- min(as.Date(index(flow.ts.est)))
   obs.min.index <- min(as.Date(index(flow.ts.obs)))
   start.index <- max(est.min.index, obs.min.index)
   
   est.max.index <- max(as.Date(index(flow.ts.est)))
   obs.max.index <- max(as.Date(index(flow.ts.obs)))
   end.index <- min(est.max.index, obs.max.index)
   
   range.str <- paste(start.index, end.index, sep="/")
   
   flow.ts.obs <- flow.ts.obs[range.str]
   flow.ts.est <- flow.ts.est[range.str]  
   
  #remove zero values
  flow.ts.obs[flow.ts.obs<=0]<- NA
  flow.ts.est[flow.ts.est<=0]<- NA
  
    
  
   
	x.lab <- "Observed Flow (cms)"
	y.lab <- "Estimated Flow (cms)"
	title.lab <- "Flow Scatterplot"
	max.flow <- max(flow.ts.obs, flow.ts.est, na.rm=T)
	min.flow <- min(flow.ts.obs, flow.ts.est, na.rm=T)
	plot(coredata(flow.ts.obs), coredata(flow.ts.est), xlim=c(min.flow,max.flow), ylim=c(min.flow,max.flow), xlab=x.lab, ylab=y.lab, main=title.lab, log="xy")
	abline(0,1, lty=2)		

 }
 
FlowAnnR2 <- function(flow.ts.obs, flow.ts.est, plot.chart=TRUE) {
  # FlowAnnR2 - function to calculate the annual flow r2 coefficient from two time-series datasets
  #
  #  Args:   flow.ts.obs - observed flow, an XTS time series with dates and flow values 
  #			flow.ts.est - estimated flow, an XTS time series with dates and flow values
  # 
  #	Output: single value of the FlowAnnR2 value
  
  # assume equal intervals and that a summation of the flow values is representative of the flow volumes.
  # force equal start and end times.
  est.min.index <- min(as.Date(index(flow.ts.est)))
  obs.min.index <- min(as.Date(index(flow.ts.obs)))
  start.index <- max(est.min.index, obs.min.index)
  
  est.max.index <- max(as.Date(index(flow.ts.est)))
  obs.max.index <- max(as.Date(index(flow.ts.obs)))
  end.index <- min(est.max.index, obs.max.index)
  
  range.str <- paste(start.index, end.index, sep="/")
  
  flow.ts.obs <- flow.ts.obs[range.str]
  index(flow.ts.obs) <- as.Date(index(flow.ts.obs))
  flow.ts.est <- flow.ts.est[range.str]
  index(flow.ts.est) <- as.Date(index(flow.ts.est)) 
  
  
  #shift the data 92 days (october, november, december) so that water year lines up with calendar year.	
  flow.ts.est <- WY2CY(flow.ts.est)
  flow.ts.obs <- WY2CY(flow.ts.obs)
  
  #calculate the sums
  sum.est <- apply.yearly(flow.ts.est, sum)	# TODO - Units need to be calculated / adjusted
  sum.obs <- apply.yearly(flow.ts.obs, sum)	# TODO - Units need to be calculated / adjusted
  
  #revert the dates back 
  sum.est <- CY2WY(sum.est)
  sum.obs <- CY2WY(sum.obs)
  
  sum.obs.mean <- mean(sum.obs)
  
  ss.err <- sum((sum.est - sum.obs)^2)
  ss.tot <- sum((sum.obs - sum.obs.mean)^2)
  
  if (plot.chart) {
    x.lab <- "Observed Volume"
    y.lab <- "Estimated Volume"
    title.lab <- "Annual Volume Comparison"
    x.lim=c(min(sum.obs,sum.est),max(sum.obs,sum.est))
    y.lim=c(min(sum.obs,sum.est),max(sum.obs,sum.est))
    
    text.labels <- as.numeric(format(index(sum.est), format = "%Y")) 
    
    plot(coredata(sum.obs), coredata(sum.est), xlim=x.lim, ylim=y.lim, xlab=x.lab, ylab=y.lab, main=title.lab)	
    abline(0,1,lty=2)		
    text(coredata(sum.obs), coredata(sum.est), text.labels, cex=0.75, pos=3) 
  }
  
  r2 <- 1- ss.err/ss.tot
}
 
 PeakAnnR2 <- function(flow.ts.obs, flow.ts.est, plot.chart=FALSE) {
# PeakAnnR2 - function to calculate the annual peak r2 coefficient from two time-series datasets
#
#	Args: 	flow.ts.obs - observed flow, an XTS time series with dates and flow values 
#			flow.ts.est - estimated flow, an XTS time series with dates and flow values
# 
#	Output: single value of the R2 value, optional graphical output

#	TODO - there is a lot of overlap with FlowAnnR2.  Could be partially combined (i.e. pass in the function name: sum, max, min, etc.)
#
	# assume equal intervals and that a summation of the flow values is representative of the flow volumes.
   # force equal start and end times.
   est.min.index <- min(as.Date(index(flow.ts.est)))
   obs.min.index <- min(as.Date(index(flow.ts.obs)))
   start.index <- max(est.min.index, obs.min.index)
   
   est.max.index <- max(as.Date(index(flow.ts.est)))
   obs.max.index <- max(as.Date(index(flow.ts.obs)))
   end.index <- min(est.max.index, obs.max.index)
   
   range.str <- paste(start.index, end.index, sep="/")
   
   flow.ts.obs <- flow.ts.obs[range.str]
   index(flow.ts.obs) <- as.Date(index(flow.ts.obs))
   flow.ts.est <- flow.ts.est[range.str]
   index(flow.ts.est) <- as.Date(index(flow.ts.est))
   
	#shift the data 92 days (october, november, december) so that water year lines up with calendar year.	
	flow.ts.est <- WY2CY(flow.ts.est)
	flow.ts.obs <- WY2CY(flow.ts.obs)
	
	#calculate the sums
	max.est <- apply.yearly(flow.ts.est, max)	# TODO - Units need to be calculated / adjusted
	max.obs <- apply.yearly(flow.ts.obs, max)	# TODO - Units need to be calculated / adjusted
	
	#revert the dates back 
	max.est <- CY2WY(max.est)
	max.obs <- CY2WY(max.obs)
	
	max.obs.mean <- mean(max.obs)

	ss.err <- sum((max.est - max.obs)^2)
	ss.tot <- sum((max.obs - max.obs.mean)^2)
 
	if (plot.chart) {
		x.lab <- "Observed Peak"
		y.lab <- "Estimated Peak"
		title.lab <- "Annual Peak Flow Comparison"
		x.lim=c(min(max.obs,max.est),max(max.obs,max.est))
		y.lim=c(min(max.obs,max.est),max(max.obs,max.est))
		
		text.labels <- as.numeric(format(index(max.est), format = "%Y")) 
		
		plot(coredata(max.obs), coredata(max.est), xlim=x.lim, ylim=y.lim, xlab=x.lab, ylab=y.lab, main=title.lab)	
		abline(0,1,lty=2)		
		text(coredata(max.obs), coredata(max.est), text.labels, cex=0.75, pos=3) 
		
	}
 
	r2 <- 1- ss.err/ss.tot
 }
 
 
 
 
  FlowAnnBias <- function(flow.ts.obs, flow.ts.est, exclude.na=F) {
# FlowAnnBias - function to calculate the annual flow volume bias  from two time-series datasets
#
#	Args: 	flow.ts.obs - observed flow, an XTS time series with dates and flow values 
#			flow.ts.est - estimated flow, an XTS time series with dates and flow values
# 
#	Output: single value of the ann flow bias value
 
    #remove observations/estimations that don't have corresponding values in other TS
    if (exclude.na){
      flow.ts.est[is.na(flow.ts.obs)]=NA
      flow.ts.obs[is.na(flow.ts.est)]=NA    
    }
    
    
 	#shift the data 92 days (october, november, december) so that water year lines up with calendar year for ease of calculation.	
	flow.ts.est <- WY2CY(flow.ts.est)
	flow.ts.obs <- WY2CY(flow.ts.obs)
	
 	#calculate the sums (volume equivalents)
	sum.est <- apply.yearly(flow.ts.est, sum, na.rm=exclude.na)	
	sum.obs <- apply.yearly(flow.ts.obs, sum, na.rm=exclude.na)	
	
	#shift the dates back
	sum.est <- CY2WY(sum.est)
	sum.obs <- CY2WY(sum.obs)
		
	#calculate the relative bias
	bias <- (mean(sum.est) - mean(sum.obs)) / mean(sum.obs)
 
 }
 
 FlowMonthBias <- function(flow.ts.obs, flow.ts.est, plot.chart=FALSE, ylim=NA, exclude.na=F) {
# FlowMonthBias - function to calculate the monthly flow volume bias  from two time-series datasets
#
#	Args: 	flow.ts.obs - observed flow, an XTS time series with dates and flow values 
#			flow.ts.est - estimated flow, an XTS time series with dates and flow values
# 
#	Output: 12 element array of flow bias values

   #remove observations/estimations that don't have corresponding values in other TS
   if (exclude.na){
     flow.ts.est[is.na(flow.ts.obs)]=NA
     flow.ts.obs[is.na(flow.ts.est)]=NA    
   }
   
	#calculate the sums (volume equivalents)
	sum.est <- apply.monthly(flow.ts.est, sum, na.rm=exclude.na)	
	sum.obs <- apply.monthly(flow.ts.obs, sum, na.rm=exclude.na)
	
	#get the month arrays for each time series (they should be identical)
	sum.est.months <- as.numeric(format(index(sum.est), format = "%m")) 
	sum.obs.months <- as.numeric(format(index(sum.obs), format = "%m")) 
   
    #assemble time-series data into a data.frame
	sum.est <- as.data.frame(sum.est)
	sum.obs <- as.data.frame(sum.obs)
	
	#set (only) column name to "flow"
	colnames(sum.est) <- "flow"
	colnames(sum.obs) <- "flow"
	
	#add new column "month" and append the month array.
	sum.est$month <- sum.est.months
	sum.obs$month <- sum.obs.months
	
	#calculate the monthly differences
	sum.diff <- sum.obs
	sum.diff$flow <- sum.est$flow - sum.obs$flow

	#application of mean value equation against the month indices.  
	sum.obs.mean <- tapply(sum.obs$flow, sum.obs$month, mean)
	sum.diff.mean <- tapply(sum.diff$flow, sum.diff$month, mean)
	
	#relative monthly bias
	monthly.bias <- sum.diff.mean / sum.obs.mean
  
	if(plot.chart){
    
    if(is.na(ylim)){
      ylim <- c(min(monthly.bias), max(monthly.bias))  
    }
    
		x.lab <- "Month"
		y.lab <- "Relative Flow Volume Bias"
		title.lab <- "Monthly Flow Volume Bias"
			
		plot(monthly.bias, type="b", xlab=x.lab, ylab=y.lab, main=title.lab, ylim=ylim)		
    grid()
    #add a horizontal line at 0
    
    abline(h=0, col="red", lty=2)
		
	}
	
	monthly.bias
	
 }
 

AvgAbsMonthBias <- function(flow.ts.obs, flow.ts.est, exclude.na=F) {
  # AvgAbsMonthBias - functino to calculate the average absolute monthly bias.
  #   Depends on results from FlowMonthBias
  #   Args: 	flow.ts.obs - observed flow, an XTS time series with dates and flow values 
  #			      flow.ts.est - estimated flow, an XTS time series with dates and flow values
  # 
  #	Output: single value, no plotting
  
  
  #Obtain monthly bias vector
  monthly.bias <- FlowMonthBias(flow.ts.obs, flow.ts.est, FALSE, NA, exclude.na)

  #calculate the avaerage absolute value of the monthly bias
  AAMB <- mean(abs(monthly.bias))
   
  AAMB
}

 
 SerialLagAutoCor <- function(flow.ts, daily.lag) {
# SerialLagAutoCor - function to calculate the serial lag coefficient of a timeseries.  
#
#	Args: 	flow.ts - flow, an XTS time series with dates and flow values 
#			daily.lag - daily integer that sets the number of serieal correlations to analyze (plus zero)
#
#	Output: data.frame with values of autocorrelation and lag (2 x daily.lag+1)

	#use autocorrelation function with plot turned off	
	x <- acf(flow.ts, daily.lag, plot=FALSE)
	output <- as.data.frame(x$acf)	
	colnames(output) <- "acf"
	output$lag <- x$lag		
	output
	
 }
 

SeialLagRMSE <- function(obs.ts, est.ts, daily.lag){
  
  sl.obs <- SerialLagAutoCor(obs.ts, daily.lag)
  sl.est <- SerialLagAutoCor(est.ts, daily.lag)
  sl.delta <- sl.est$acf - sl.obs$acf
  sl.rmse <- sqrt(mean((sl.delta)^2))

  sl.rmse
}
 
 SerialLagAutoCor.Plot  <- function(flow.ts.obs, flow.ts.est, daily.lag) {
# SerialLagAutoCor.Plot - function to plot the serial lag coefficient of a timeseries.  
#
#	Args: 	flow.ts.obs - observed flow, an XTS time series with dates and flow values 
#			flow.ts.est - estimated flow, an XTS time series with dates and flow values 
#			daily.lag - daily integer that sets the number of serieal correlations to analyze (plus zero)
#
#	Output: generates graphical output

	daily.lag.obs <- SerialLagAutoCor(flow.ts.obs, daily.lag)
	daily.lag.est <- SerialLagAutoCor(flow.ts.est, daily.lag)
	
	x.lab <- "Lag"
	y.lab <- "Autocorrelation"
	title.lab <- "Serial Lag Autocorrelation"
	
	plot(daily.lag.obs$lag, daily.lag.obs$acf, type="b", ylim=c(min(daily.lag.obs$acf, daily.lag.est$acf),1), xlab=x.lab, ylab=y.lab, main=title.lab)
	lines(daily.lag.est$lag, daily.lag.est$acf, type="b", col="red")	
	grid()
	
	legend(
		"topright", 
		c("observed", "estimated"), 
		lty=c(1,1),
		pch=c(1,1),
		col=c("black","red"), 	
	)	

	
 }
 
 AetPet.CumPlot  <- function(AET.ts, PET.ts) {
# AetPet.CumPlot - function to plot the AET/PET cumulative plots for the simulation
#
#	Args: 	AET.ts - AET time series
#			PET.ts - PET time series
#
#	Output: generates graphical output
 
	# apply cumulative sum function to PET and AET time series
	PET.ts.cs <- cumsum(PET.ts)
	AET.ts.cs <- cumsum(AET.ts)

	# plot labels
	y.lab <- "AET / PET (cms)"
	title.lab <- "Basin Cumulative AET / PET"
	
	# generate the plot
	plot(PET.ts.cs, ylab=y.lab, main=title.lab)
	lines(AET.ts.cs, col="red")
	
	legend(
		"topleft", 
		c("PET", "AET"), 
		lty=c(1,1),		
		col=c("black","red"), 	
	)	

 }
 
 RunoffContribution.CumPlot <- function(rainfall.q.ts, snow.q.ts, glacier.q.ts) {
# RunoffContribution.CumPlot - function to plot the AET/PET cumulative plots for the simulation
#
#	Args: 	rainfall.q.ts - Rainfall runoff time series
#			snow.q.ts - Snowmelt runoff time series
#			glacier.q.ts - Glacier runoff time series
#
#	Output: generates graphical output
 
 	# apply cumulative sum function to PET and AET time series
	rainfall.q.ts.cs <- cumsum(rainfall.q.ts)
	snow.q.ts.cs <- cumsum(snow.q.ts)
	glacier.q.ts.cs <- cumsum(glacier.q.ts)

	# plot labels
	y.lab <- "Runoff (cms)"
	title.lab <- "Cumulative Flow Contributions"
	
	y.lim <- c(0,max(snow.q.ts.cs,rainfall.q.ts.cs,glacier.q.ts.cs))
	
	# generate the plot
	plot(snow.q.ts.cs, ylim=y.lim, ylab=y.lab, main=title.lab)
	lines(rainfall.q.ts.cs, col="red")
	lines(glacier.q.ts.cs, col="blue")
	
	legend(
		"topleft", 
		c("Snow", "Rain", "Glacier"), 
		lty=c(1,1,1),		
		col=c("black","red", "blue"), 	
	)	

 }
 
  RunoffContribution <- function(rainfall.q.ts, snow.q.ts, glacier.q.ts, plot.chart=FALSE) {
# RunoffContribution - calculate the annual runoff contributions. 
#	*** TODO *** this should be done as an ARRAY of TSs with the names in a vector that follows
#				 currently this whole function is in triplicate!
#
#	Args: 	rainfall.q.ts - Rainfall runoff time series
#			snow.q.ts - Snowmelt runoff time series
#			glacier.q.ts - Glacier runoff time series
#
#	Output: generates graphical output
 
 	# apply cumulative sum function to PET and AET time series
	rainfall.q.ts.cs <- cumsum(rainfall.q.ts)
	snow.q.ts.cs <- cumsum(snow.q.ts)
	glacier.q.ts.cs <- cumsum(glacier.q.ts)

		
	#shift from water year to calendar year
	rainfall.q.ts.cs <- WY2CY(rainfall.q.ts.cs)
    snow.q.ts.cs <- WY2CY(snow.q.ts.cs)
	glacier.q.ts.cs <- WY2CY(glacier.q.ts.cs)
  
	#determine annual maxima
  	rainfall.yr.max <- apply.yearly(rainfall.q.ts.cs, max)
	snow.yr.max <- apply.yearly(snow.q.ts.cs, max)
	glacier.yr.max <- apply.yearly(glacier.q.ts.cs, max)
  
  	#shift back from calendar year to water year
	rainfall.yr.max <- CY2WY(rainfall.yr.max)
	snow.yr.max <- CY2WY(snow.yr.max)
	glacier.yr.max <- CY2WY(glacier.yr.max)
	
	#preserve dates for recreation of XTS later
	dates <- index(rainfall.yr.max)
	
	#add zero values to front of vectors
	rainfall.yr.max <- c(0,rainfall.yr.max)
	snow.yr.max <- c(0,snow.yr.max)
	glacier.yr.max <- c(0,glacier.yr.max)
	
	
	#incremental difference calculations
	rainfall.diff <- as.vector(rainfall.yr.max[-1]) - as.vector(rainfall.yr.max[-length(rainfall.yr.max)])
	snow.diff <- as.vector(snow.yr.max[-1]) - as.vector(snow.yr.max[-length(snow.yr.max)])
	glacier.diff <- as.vector(glacier.yr.max[-1]) - as.vector(glacier.yr.max[-length(glacier.yr.max)])
	
	#calculate total annual runoff sums
	sum.flow <- rainfall.diff + snow.diff + glacier.diff
	
	#calculate relative contributions
	rainfall.rel <- rainfall.diff / sum.flow
	snow.rel <- snow.diff / sum.flow
	glacier.rel <- glacier.diff / sum.flow
	
	
	if (plot.chart) {
		# plot labels
		y.lab <- "Relative Contribution"
		title.lab <- "Annual Flow Contributions"
		rel.flows <- t(cbind(rainfall.rel, snow.rel, glacier.rel))
		years <- as.numeric(format(dates, "%Y")) 
		colnames(rel.flows)<- years
		barplot((rel.flows), main=title.lab, xlab="Year", xlim=c(0,length(years)*1.5), col=c("darkblue","red","green"))
		
		legend(
			"topright",
			c("Rain", "Snow", "Glacier"),
			fill=c("darkblue","red","green") 	
		)
			
	}
	
	rainfall.rel

 }
 
 RunoffCoefficient.CumPlot <- function(rainfall.ts, runoff.ts) {
 # RunoffCoefficient.CumPlot - function to plot the Rainfall/Runoff cumulative plots for the simulation
#
#	Args: 	rainfall.ts - Rainfall time series
#			runoff.ts - Runoff time series
#
#	Output: generates graphical output
 
 	rainfall.ts.cs <- cumsum(rainfall.ts)
	runoff.ts.cs <- cumsum(runoff.ts)
 
 	# plot labels
	y.lab <- "Rainfall / Runoff (cms)"
	title.lab <- "Cumulative Rainfall / Runoff Profile"
 
 	# generate the plot
	plot(runoff.ts.cs, ylab=y.lab, main=title.lab, ylim=c(0, max(runoff.ts.cs, rainfall.ts.cs)) )
	lines(rainfall.ts.cs, col="red")	
 
 }
 
  RunoffCoefficient <- function(rainfall.ts, runoff.ts, plot.chart=FALSE) {
  
   	#calculate cumulative sums
	rainfall.ts.cs <- cumsum(rainfall.ts)
	runoff.ts.cs <- cumsum(runoff.ts)
 
	
	#shift from water year to calendar year
	rainfall.ts.cs <- WY2CY(rainfall.ts.cs)
    runoff.ts.cs <- WY2CY(runoff.ts.cs) 
  
	rainfall.yr.max <- apply.yearly(rainfall.ts.cs, max)
	runoff.yr.max <- apply.yearly(runoff.ts.cs, max)
  
  	#shift back from calendar year to water year
	rainfall.yr.max <- CY2WY(rainfall.yr.max)
	runoff.yr.max <- CY2WY(runoff.yr.max) 
	
	#preserve dates for recreation of XTS later
	dates <- index(rainfall.yr.max)
	
	#add zero values to front of vectors
	rainfall.yr.max <- c(0,rainfall.yr.max)
	runoff.yr.max <- c(0,runoff.yr.max)
	
	#incremental difference calculations
	rainfall.diff <- as.vector(rainfall.yr.max[-1]) - as.vector(rainfall.yr.max[-length(rainfall.yr.max)])
	runoff.diff <- as.vector(runoff.yr.max[-1]) - as.vector(runoff.yr.max[-length(runoff.yr.max)])

	#calculate rainfall-runoff coefficient for each water year
	rr.diff <- runoff.diff/rainfall.diff	
  
	#plot if selected
	if(plot.chart){		
		y.lab <- "Runoff / Rainfall"
		x.lab <- ""
		title.lab <- "Runoff Coefficient by Water Year"
		plot(dates, rr.diff, ylim=c(0,1), ylab=y.lab, xlab=x.lab, main=title.lab)
		abline(h=mean(rr.diff), lty=2)
	}

	#return the rainfall runoff as an annual time-series
	rr.diff <- xts(rr.diff, dates)
  }
  
  
  WY2CY <- function (in.ts) {
# WY2CY - function to shift a time series from water year to calendar year
#			largely to take advantage of the apply.yearly xts functions
#
#	Args: 	in.ts - any time series
#
#	Output: a time series

  	index(in.ts) <- as.Date(index(in.ts) + 92)
	in.ts
  
  }
  
  CY2WY <- function (in.ts) {
# CY2WY - function to shift a time series from calendar year to water year
#			used as get back to water year after an xts function has been applied after a WY2CY shift
#
#	Args: 	in.ts - any time series
#
#	Output: a time series

  	index(in.ts) <- as.Date(index(in.ts) - 92)
	in.ts
  
  }
  
  
objectiveFunction <- function (objname, obs, sim) {
 
  # this computes various objective functions based upon observed and
  # computed series. All results are rounded to 4 decimal places
  # but all are translated into maximization functions
 
 
  MAE <- function(obs, sim) {
    stat <- mean( abs(sim - obs) )
    return ( round(stat, digits=4) )
  }
 

 
  # returns bias.
  BIAS <- function(obs, sim) {
    stat <- mean((sim - obs))
    return ( round(stat, digits=4) )
  }
 
  # returns Nash and Sutcliffe efficiency E.  (maximization objective)
  E2 <- function(obs, sim) {
    stat <- 1 - (sum((obs - sim)^2) / sum((obs - mean(obs))^2))
    stat <- round(stat, digits=4)
    return (stat)
  }
 
  # returns efficiency/relative volume measure
  # see Lindstrom et al 1997 J.Hydrol. 201, 272-288
  ERV <- function(obs, sim) {
    weight <- 0.1
    eff <- 1 - (sum((obs - sim)^2) / sum((obs - mean(obs))^2))
    rd <- (mean(obs) - mean(sim)) / mean(obs)
    stat <- round(eff - weight * abs(rd), digits=4)
    return (stat)
  }
 
  # returns square of Pearson's product-moment correlation coefficient
  R2 <- function(obs, sim) {
    stat <- round( (cor(sim, obs))^2, digits=4 )
    return (stat)
  }
 
  # main function call
  #-------------------------------------------
  if (toupper(objname) == 'MAE') return ( MAE(obs,sim) )
  else if (toupper(objname) == 'BIAS') return ( BIAS(obs,sim) )
  else if (toupper(objname) == 'E') return ( E2(obs,sim) )
  else if (toupper(objname) == 'ERV') return ( ERV(obs,sim) )
  else if (toupper(objname) == 'MARE')  return ( MARE(obs,sim) )
  else if (toupper(objname) == 'R2') return ( R2(obs,sim) )
 
}  # EndFunction: objectiveFunction()

   