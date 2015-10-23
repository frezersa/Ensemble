#
# Frequency Library (libFreq.r)
#
# A list of functions that have been collected to assist in flood frequency analysis.  Used in a number of scripts.

source("rlib\\libStr.r")
source("rlib\\libFileIO.r")

library (lmom)
library (extremevalues)
library (psych)



EvDist <- function (maxvec, dist.type) {
#
# ev.dist
# 
# Function for calculating the extreme values parameters using lmoments
# maxvec - the vector of the maximum values
# type - the distribution type
#		1 - GEV
#		2 - PE3
#		3 - LPE3
#		4 - LN3
  
  #remove NA or zero flow values  
  maxvec <- na.omit(maxvec)
  maxvec <- maxvec[maxvec>0]

  #sort the vectors
  smom <- samlmu( maxvec, sort.data = TRUE )
	log.smom <- samlmu( log(maxvec), sort.data = TRUE )
	
	if(dist.type==1){
		ev.par <- pelgev(smom)
	
	} 
	else if(dist.type==2) {
		ev.par <- pelpe3(smom)
	
	} 
	else if(dist.type==3) {
		ev.par <- pelpe3(log.smom)
	
	} 
	else {
		ev.par <- pelln3(smom)
	
	}
	
	ev.par
}

EvDistPlot <- function (para, dist.type, format.str="") {

	
	if(dist.type==1){
		evdistq(quagev, para, col = 'black')
	
	} 
	else if(dist.type==2) {
		evdistq(quape3, para, col = 'black')
	
	} 
	else if(dist.type==3) {
		evdistq(quaLPE3, para, col = 'black')
	
	} 
	else {
		evdistq(qualn3, para, col = 'black')
	
	}
	
}


EVCalcQuantiles <- function (ev.list, dist.index, prob.val, rm.out=F){
  #
  # EVCalcQuantiles 
  #
  #  Takes a vector of maximum flow, fits an EV distribution to the data, and oupututs 
  #	estimates of values at return intervals (probabilities)
  #
  #	Args:
  #		ev.list - ev analysis list from EvAnalysis
  #		dist.index - the index for the distributions 
  #			1 - GEV
  #			2 - PE3
  #			3 - LPE3
  #			4 - LN3  
  #		prob.val - a vector of the probabilities being examined.
  #	
  #	Return:
  #		an array of EV estimates of size prob.val
  #    
  
  #
  
  #extract data array from the ev.list
  data1 <- ev.list$data
  
  #remove zero or negative flows for LP3
  if(dist.index==3){
    data1<- data1[data1$zero==F,]
  }
  
  #remove outliers if necessary
  if(rm.out){
    data1<- data1[data1$zero==F,]
    data1<- data1[data1$low==F,]
    data1<- data1[data1$high==F,]  
  }
  
  #Remove any NA values and sort.  
  
  
  flow.max <- data1$flow
  
  flow.max <- na.omit(flow.max)
  flow.max.sort <- sort(coredata(flow.max))
  
  #Calculate the distribution parameters
  ev.pars <- EvDist(flow.max.sort, dist.index)
  
  #Calculate the quantiles 
  ev.quantiles <- DistQuantile(prob.val, ev.pars, dist.index)  
  
}


# ?
PlotGEV <- function(maxvec, color1) {
	gevtemp <- gev(maxvec)
	evdistq(quagev,gevtemp,col=color1)
	exc1 = quagev(exc, gevtemp)
	exc1
}

# ?
SummerTS <- function(ts, ep){
	ts <- na.omit(ts)	#remove any NA values
	pmax <- period.max(ts, ep)	 # find the maximum values in the periods defined by ep
	vec <- pmax[seq(2, length(pmax), 3)] #hard code summer sequence
	vec
}

MaxTS2Vec <- function(ts,ep){
	
    vec <-summerts(ts,ep)
	vec <- as.vector(vec)	
	vec[vec<=0.0]<-NA #now remove zero values
	vec <- sort(vec)
	vec

}

MaxVec <- function (f, str) {
	vec <- tapply(f[[str]], f$YEAR,max); f[str]
	vec[vec<=0.0]<-NA
	vec<-sort(vec)
	vec
}



DistQuantile <- function(f, para, dist.type) {
# Generic Quantile Function
	if(dist.type==1){
		ev.quantile <- quagev(f, para)
	
	} 
	else if(dist.type==2) {
		ev.quantile <- quape3(f, para)
	
	} 
	else if(dist.type==3) {
		ev.quantile <- quaLPE3(f, para)
	
	} 
	else {
		ev.quantile <- qualn3(f, para)
	
	}
	
	ev.quantile

}


quaLPE3 <- function (f, para) {
# quantile function for log Pearson type III distribution
  return ( exp(quape3(f, para)) )
}





QdfEvent <- function(flow.ts, daily.vals) {

	dv.count <- 0
	for(dv in daily.vals) { 
		
		dv.count <- dv.count + 1 									#interval counter
		flow.filt <- filter(flow.ts, rep(1/dv, dv), sides=2) 
		
		max.flow <- max(flow.filt, na.rm = TRUE)
		
		if (dv.count==1) {
			Qdf.event <- max.flow
		}
		else {
			Qdf.event <- cbind(Qdf.event, max.flow)
		}
		
	}
	
	colnames(Qdf.event) <- daily.vals
	Qdf.event

}


QdfMatrix <- function(orig.flow.ts, dist.index, daily.vals, prob.val){
#
# QdfMatrix
#
#	Will take a time series, from a file name, and apply a known frequency distribution
#	and extract the daily average flow values for a number of probabilities
#
#	Args:
#		file.name - path to a file name
#		dist.index - the index for the distributions 
#			1 - GEV
#			2 - PE3
#			3 - LPE3
#			4 - LN3
#		daily.vals - a vector for the daily averaged values
#		prob - a vector of the probabilities being examined.
#	
#	Return:
#		a matrix of size (prob, daily.vals)
#


	#Generating Plot Flag
	kPlot <- FALSE

	#Set file name - (could be loaded from an argument eventually)
	#file.name <- "flow.data\\5OB007_Daily_Flow_ts.csv"
			

	#Constant array of daily values.
	#daily.vals <- c(1,3,5,7,11,15,21,31)
	#Constant arry of probaliites 
	#prob <- c(0.99, 0.98, 0.95, 0.90)

	#Specify Distribution 
	#dist.index <- 4

	#Load the file and populate the original flow time series.




	dv.count <- 0

	for(dv in daily.vals) { 
		
		dv.count <- dv.count + 1 									#interval counter
		flow.filt <- filter(orig.flow.ts, rep(1/dv, dv), sides=2)  	#averaging over the specified daily values (dv)
		flow.filt.ts <- xts(flow.filt, index(orig.flow.ts))			#re assemble as a time-series
		
    #Get annual maxima array using XTS
		flow.max.annual <- apply.yearly(na.omit(flow.filt.ts), max) #determine the maximum flow for each year

    #Calculate the quantiles using the annual flow max fector, selected distribution and the recurrence interval vectors. 
    ev.quantiles <- EVCalcQuantiles(flow.max.annual, dist.index, prob.val)    
		
		#Generate a plot
		if (kPlot) {
			plot.max <- max( c(flow.max.annual.sort, ev.quantiles))
			evplot(flow.max.annual.sort, ylim = c(0,plot.max))
			EvDistPlot(ev.pars, dist.index, "")
		}
		
		#assemble a matrix of the quantiles for each interval
		
		if (dv.count==1) {
			ev.quantiles.matrix <- ev.quantiles
		}
		else {
			ev.quantiles.matrix <- cbind(ev.quantiles.matrix, ev.quantiles)
		}
	}

	#Attach appropriate names to the rows (the probabilities)
	colnames(ev.quantiles.matrix) <- daily.vals  #attach column names 
	rownames(ev.quantiles.matrix) <- prob.val		#attach rown names

	#return the matrix back.
	ev.quantiles.matrix

}



EvOutliersGrubbs <- function(index.flow){
  #
  # EvOutliers
  #
  #  uses the Grubbs and Beck (1972) method for identifying outliers
  #	 also done in teh CFA analysis by EC. (10% signficance level)
  #
  #	Args:
  # - index.flow - a data.frame of the maximum flow values with an "index" and "flow" field
  # 
  #	
  #	Return:
  # - a dataset with the original matrix and a true-false field
  #   indicating if the dataset is an outlier.
  #
  #
 
  
  #remove the zero and negative values  
  flow.pos <- index.flow[index.flow$flow>0,]  
  n <- length(flow.pos$flow)
  
  #estimate of the parameter KnS (see CFA Manual, p 10)
  y = -3.62201 + 6.28446*n^(0.25) - 2.49835*n^(0.5) + 0.491436*n^(0.75) - 0.037911*n
  
  #calculate the natural log
  x <- log(flow.pos$flow)
  
  #calculate mean of the log data
  x.mean <- mean(x)  
  
  #upper and lower limits of outliers
  x.h <- exp(x.mean + y)
  x.l <- exp(x.mean - y)
  
  x.low <- x < x.l
  x.high <- x > x.h
  
  
  #assemble the dataframe with the new high and low data
  x.return <- cbind(flow.pos, low=x.low, high=x.high)   
  #merge with the original index.flow data to preserve the same rows originally submitted
  x.return <- merge(index.flow,x.return, all.x=T)
  as.data.frame(x.return)
  
  
}

EvOutliersMVDL <- function(index.flow){
  
# uses "extremevalues" package develoed by mark vanderloo
  
  #remove non positive flows
  flow.pos <- index.flow[index.flow$flow>0,]  
  
  #get the row count
  n <- length(flow.pos$flow)      
  
  #calculate the natural log
  x <- log(flow.pos$flow)
  
  mvdl <- getOutliers(x, method="I")
  
  x.l <- mvdl$limit["Left"]
  x.h <- mvdl$limit["Right"]
  
  x.low <- x < x.l
  x.high <- x > x.h
  
  #assemble the dataframe with the new high and low data
  x.return <- cbind(flow.pos, low=x.low, high=x.high)   
  #merge with the original index.flow data to preserve the same rows originally submitted
  x.return <- merge(index.flow,x.return, all.x=T)
  as.data.frame(x.return)
}



EvSkew <- function(index.flow, rm.out=FALSE){
  # EvSkew
  
  # calculation of the skew values for the max.flow data
  # Args:
  #   max.flow - the index.flow data (must also include low, high and zero fields)
  # Return:
  #   skew - a named list including the skew values of the natural and log transformed datasets.
  
  
  data1<- index.flow[index.flow$zero==F,]  
  
  #if remove outliers selected take out the low and high outliers as identified
  if (rm.out){
    data1 <- data1[data1$low==F,]
    data1 <- data1[data1$high==F,]
  }
  
  data1<- data1$flow
  
  x <- skew(data1)
  lnx <- skew(log(data1))    
  skew <- list(x=x, lnx=lnx)  
    
}

EvHistNorm <- function(ev.list, rm.out=F, title="histogram", xlab="xlab", col.hist="red", col.line="black"){
  # EvHistNorm
  #
  # Generate a histogram of the dataset and the plot of the best fit normal distribution.
  # which starts by taking the natural log of flow data
  
  data1 <- ev.list$data
  
  #remove zero flow
  data1 <- data1[data1$zero==F,]
  
  #remove outliers if selected
  if(rm.out){
    data1 <- data1[data1$low==F,]
    data1<- data1[data1$high==F,]      
  }
  
  max.flow <- data1$flow
  
  lnx<- log(max.flow)
  h<- hist(lnx, main=title, xlab=xlab, col=col.hist)
  
  xfit<-seq(min(lnx),max(lnx),length=100) 
  yfit<-dnorm(xfit,mean=mean(lnx),sd=sd(lnx))   
  yfit <- yfit*diff(h$mids[1:2])*length(lnx)
  
  lines(xfit,yfit, col=col.line, lwd=2)
  
}

EvOutliers <- function(max.flow, method="Grubbs"){
  # EvOutliers 
  #
  #   wrapper functions for other outliers functions and to 
  #   identify zero (or negative) flows

  if(method=="MVDL"){    
    x<- EvOutliersMVDL(max.flow)
    
  }else if(method=="Grubbs"){    
    x<- EvOutliersGrubbs(max.flow)    
    
  }else{    
    stop(paste("EvOutliers - error in method definition:", method))          
  }  
  
  y <- EvZeroFlows(x)
}

EvZeroFlows <- function(index.flow){
  # EvZeroFlows
  #
  #
  # 
  
  x.z <- index.flow$flow <= 0  
  x.return <- cbind(index.flow, zero=x.z)    
  as.data.frame(x.return)
  
}

EvAnalysis <- function(index.flow, outlier.method="Grubbs"){
  #EvAnalysis
  # super-wrapper for outlier detection, stats, etc. combined into an object (list)
  # that can be used for future analysis, plot generation etc.
    
  
  x<- EvOutliers(index.flow, method=outlier.method)  
  s <- EvSkew(x)
  s.out <- EvSkew(x, rm.out=T)
  count.low <- sum(x$low, na.rm=T)
  count.high <- sum(x$high, na.rm=T)
  count.zero <- sum(x$zero, na.rm=T)
  count.total <- length(x[,"flow"])
  
  count <- list(total=count.total, low=count.low, high=count.high, zero=count.zero)    
  return.x <- list(data=x, outlier.method=outlier.method, count=count, skew=s, skew.no.outliers=s.out)
      
}

EvQqPlotNorm <- function (ev.list, rm.out=F, title="Q-Q Plot", xlab="Theoretical Quantiles", ylab="Sample Quantiles"){
  #EvQqPlotNorm
  #
  # generate a qq plot of the log data aginast the normal curve, with or without outliers considered.
  #
  # Args: ev.list - a list from the EvAnalysis output.
  
  
  #get the data frame
  data1 <- ev.list$data
  
  #remove zero and negative values
  data1 <- data1[data1$zero==F,]
  #get the logarithmic dataset
  lnx<- log(data1$flow)
  
  #generate outlier indices
  low.index <- data1[order(data1$flow),"low"]
  high.index <- data1[order(data1$flow),"high"]
  
  #sort and collect the plotting data
  sort.lnx <- sort(lnx)
  sort.lnx.out <- sort.lnx
  sort.lnx.out[low.index] <- NA
  plot.x <- qnorm(ppoints(lnx))
  
  #set the plotting limits
  y.lim <- c(min(lnx), max(lnx))  
  x.lim <- c(min(plot.x), max(plot.x))
    
  
  if(rm.out==F){
    plot(plot.x[!low.index], sort.lnx[!low.index], xlim=x.lim, ylim=y.lim, xlab=xlab, ylab=ylab, main=title)
    points(qnorm(ppoints(lnx))[low.index], sort.lnx[low.index], col="red", pch=2)
    qqline(lnx)
    
    legend(
      x = 'topleft',
      legend = c("Data Points", "Outliers"),
      col = c("black", "red"),
      pch = c(1,2),
      lty = c(-1,-1)
    )    
    
  } else{
    
    #now produce a plot with only the outliers. 
    
    plot.x.out <- qnorm(ppoints(na.omit(sort.lnx.out)))
    plot(plot.x.out, na.omit(sort.lnx.out), xlim=x.lim, ylim=y.lim, main=title, xlab=xlab, ylab=ylab)
    qqline(na.omit(sort.lnx.out))
    
    legend(
      x = 'topleft',
      legend = c("Data Points"),
      col = c("black"),
      pch = c(1),
      lty = c(-1)
      
    )  
    
  }
  
}

EvPlotDist <- function(ev.list, dist.type, rm.out=F, title="EV Plot"){
  #EvPlotDist
  #
  # Generate an evplot for a specified distribution 
    
  data1<- ev.list$data
  
  #remove zero or negative flows for LP3
  if(dist.type==3){
    data1<- data1[data1$zero==F,]
  }
  
  #remove outliers if necessary
  if(rm.out){
    data1<- data1[data1$zero==F,]
    data1<- data1[data1$low==F,]
    data1<- data1[data1$high==F,]  
  }
  
  x.flow <- data1$flow
  
  y <- EvDist(x.flow, dist.type)
  
  evplot(x.flow, main=title)
  EvDistPlot(y, dist.type)  
  
}



EvCPA <- function (){

  
  }
