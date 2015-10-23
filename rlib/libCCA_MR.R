#****************************************************************************
# Name: libCCA_MR
# Date written: October 2,2012
# Written By: James Bomhof
# Modified By: Wayne Jenkinson
# Description: The code performs a CCA analysis to find the most correlated stations
#   with respect to a target station. It was written to input a multivariable flow dataset (Y) and 
#   a multivariable physiographic dataset (X). The code could easily be adjusted for other predictions.
#   The code utilizes a 'neighbour' function which is given in the script. After the best neighbouring stations
#   are found, a jack-knife analysis is done using a linear regression to predict flow at the target 
#   station. This is looped for all stations and multiple values of alpha. Finally the errors are 
#   calculated and output to a csv so the where the optimal alpha value can be chosen.
#******************************************************************************

library(CCA)


#**************************************************************
neighbour <- function(X,Y,Xtarg,alpha,index, col.list=c(2,4,5,6,8,10)){
  #function to calculate the canonical correlations functions btwn
  #two multivariable datasets (X&Y) and find best correlated neighbouring stations
  #Standardize the Data
  # Args:
  #  	X - physiographic data
  #		Y - flow data
  #		Xtarg - target vector of physiographic data
  #		alpha - probability (for neighbourhood)
  #		index - a unique identifier for station list
  #		col.list - a subset of the flow columns to be used for CCA - default to use 6 as suggested by Ouarda 
  #
  Mean <- apply(X,2,mean)
  STD <- apply(X,2,sd)
  
  nonzerocols <- names(STD[STD!=0]) #check for columns where std dev ==0
  Xtarg <- subset(Xtarg, select=nonzerocols) #remove zero columns
  X <- subset(X,select=nonzerocols) #remove zero columns
  
  Xtarg <-(Xtarg-Mean)/STD #Xtarg must be standardized against the whole X dataset (hence can't use scale())
  
  X <-scale(X)
  Y <-scale(Y)
  
  #Perform CCA and calculate key values
  Y <- Y[,col.list] 
  data <- cc(X, Y) #perform CCA
  DF <- length(data$cor) #degrees of freedom = # of canonical functions
  lambda <- diag(DF) * data$cor #used for calculating mahalanobis distance
  Xtscore <- t(as.matrix(Xtarg) %*% as.matrix(data$xcoef)) #target score
  chi2 <- qchisq(1-alpha,DF) #critical distance from target(stations outside this line are excluded
  
  #Caculate mahalanobis distance see eqn 7 of Ouarda et al., Dec2000
  W <- data$scores$yscores
  V <- lambda %*% Xtscore
  S <- diag(DF) - lambda^2
  Q <- mahalanobis(W,V,S)
  
  #Output logical vector saying which stations are 'nearest neighbours'
  NeighYN<-vector(mode = "logical",length=nrow(X))
  NeighYN[Q<=chi2]<-T
  returnvalue <- as.data.frame(cbind(index,NeighYN,Q))
  return(returnvalue)
}
#***************************************************************


#***************************************************************
#Function to calculate mean daily value from FDC or PDC
#***************************************************************

library(signal)
library(pracma)
DailyMeanFDC <- function(FDC){
  if(any(is.na(FDC[1:12]))){Area<-NA}else{
    if(any(is.na(FDC[13:17]))){Value<-min(which(is.na(FDC[13:17])))+12;FDC[Value:17]<-FDC[Value-1]}
    Exceed <- c(0.0001,.001,.005,.01,.05,.1,.2,.3,.4,.5,.6,.7,.8,.9,.95,.99,.9999) #test data
    #Points <-seq(0,1,1/999)
    #InterpPoints <- pchip(Exceed,as.numeric(FDC),Points)
    #Area <-abs(trapz(x=Points,y=InterpPoints))
    Area<-abs(trapz(x=Exceed,y=FDC))
  }
  return(Area) 
}

#input 17 value vector
# DailyMeanFDC <- function(FDC){
#   #Exceed <- c(0.0001,.001,.005,.01,.05,.1,.2,.3,.4,.5,.6,.7,.8,.9,.95,.99,.9999) #test data
#   Space <- c(0.00055,.00245,.0045,.0225,.045,.075,.1,.1,.1,.1,.1,.1,.1,.075,.045,.02495,.00505) #space inbetween FDC intervals 
#   Area<-sum(Space*FDC,na.rm=T)
#   return(Area)
# }


DailyMeanMMF <-function(MMF){
  Days <- c(31,28,31,30,31,30,31,31,30,31,30,31)
  Average <- sum(MMF*Days)/365
  return(Average)
}


FDCSUM <-function(RealFDC,EstFDC=c(rep(0,17))){ 
  if(is.vector(RealFDC)){RealFDC<-as.data.frame(t(RealFDC))}
  if(is.vector(EstFDC)){EstFDC<-as.data.frame(t(EstFDC))}
  
  if(!is.null(nrow(RealFDC))){RealDailyMeans<-apply(RealFDC,1,DailyMeanFDC)}else{RealDailyMeans<-sum(RealFDC)}
  if(!is.null(nrow(EstFDC))){EstDailyMeans<-apply(EstFDC,1,DailyMeanFDC)}else{EstDailyMeans<-sum(EstFDC)}

  Ratio<-sum(RealDailyMeans,EstDailyMeans)/max(RealDailyMeans)
  NewFDC <- as.numeric(Ratio*RealFDC[which.max(RealDailyMeans),])
  return(NewFDC)
  }

#Stats on estimated values
CalcStats<-function(Estimate,Actual){
  Mean.Actual<-mean(Actual,na.rm=T)
  Dev <- Actual - Mean.Actual
  SST <- sum(Dev^2,na.rm=T)
  
  Err <- Actual - Estimate
  RelErr <- Err/Actual
  SSE <- sum(Err^2,na.rm=T)
  NASH <- 1-SSE/SST
  RMSE <- (mean(Err^2,na.rm=T))^.5
  RRMSE <- (mean(RelErr^2,na.rm=T))^.5
  Bias <- (mean(Err,na.rm=T))
  
  Results<-c(RMSE=RMSE,RRMSE=RRMSE,Bias=Bias,NASH=NASH)
  return(Results)
}

BankfullFlow <-function(data){
  Flows<-as.xts(as.data.frame(flow$daily$value),order.by = flow$daily$date) #change to timeseries
  Flows<-na.omit(Flows) #get rid of NA values

  YearFlows<-WY2CY(Flows) #convert to water year (Oct 1 - Sept 31)
  MaxFlows<-apply.yearly(YearFlows,max) #get maximum flow for each year
  MaxFlows<-na.omit(MaxFlows)

  n<-length(MaxFlows)-2 #calculate # of years
  if(n>10){ #if there is 10+ years data, calculate flood frequency
  
    MaxFlows<-MaxFlows[c(-1,-length(MaxFlows))] #omit first year and last year which only includes partial months
    names(MaxFlows)<- "AnnualMax"
    MaxFlows<-sort(as.vector(MaxFlows))
    rank <- seq(n,1,-1)
    logMaxFlows <-log(MaxFlows)
    returnperiod <- (n+1)/rank
    exceedance<-1/returnperiod
    y<- -log(-log(1-exceedance))
 
    jam<-as.data.frame(cbind(MaxFlows,returnperiod,y))
    regress<-lm(MaxFlows~y,data=jam[jam$returnperiod>1.1&jam$returnperiod<2,])

  
    #Predict 1.5 year flow
    newdata<-jam[1,]
    newdata[1,2:3]<-c(1.5,-log(-log(1 - 1/1.5)))
    newdata[1,1]<-predict.lm(regress,newdata)
    return(newdata[1,1])
    }else(return(NA))
}



# Multiple plot function
#
# ggplot objects can be passed in ..., or to plotlist (as a list of ggplot objects)
# - cols:   Number of columns in layout
# - layout: A matrix specifying the layout. If present, 'cols' is ignored.
#
# If the layout is something like matrix(c(1,2,3,3), nrow=2, byrow=TRUE),
# then plot 1 will go in the upper left, 2 will go in the upper right, and
# 3 will go all the way across the bottom.
#
multiplot <- function(..., plotlist=NULL, file, cols=1, layout=NULL) {
  require(grid)
  
  # Make a list from the ... arguments and plotlist
  plots <- c(list(...), plotlist)
  
  numPlots = length(plots)
  
  # If layout is NULL, then use 'cols' to determine layout
  if (is.null(layout)) {
    # Make the panel
    # ncol: Number of columns of plots
    # nrow: Number of rows needed, calculated from # of cols
    layout <- matrix(seq(1, cols * ceiling(numPlots/cols)),
                     ncol = cols, nrow = ceiling(numPlots/cols))
  }
  
  if (numPlots==1) {
    print(plots[[1]])
    
  } else {
    # Set up the page
    grid.newpage()
    pushViewport(viewport(layout = grid.layout(nrow(layout), ncol(layout))))
    
    # Make each plot, in the correct location
    for (i in 1:numPlots) {
      # Get the i,j matrix positions of the regions that contain this subplot
      matchidx <- as.data.frame(which(layout == i, arr.ind = TRUE))
      
      print(plots[[i]], vp = viewport(layout.pos.row = matchidx$row,
                                      layout.pos.col = matchidx$col))
    }
  }
}


MCStats <- function(VorList){
#*****************************************************************
#Calculate magnitude of  confidence
Conf<-data.frame(matrix(NA,length(VorList),ncol(VorList[[1]])))
row.names(Conf)<-names(VorList)
names(Conf)<-c(paste("FDC",seq(1,17,1),sep=""))#,"MAF")
Median<-Conf
Mean<-Conf
Upper<-Conf
Lower<-Conf


pb <- txtProgressBar(min = 0, max = length(VorList), style = 3)
for(i in 1:length(VorList))
{
  #Calculate Stats
  Conf[i,]<-as.numeric((diff(apply(VorList[[i]],2,quantile,probs=(c(.025,.975)),na.rm=T)))/(apply(VorList[[i]],2,median,na.rm=T)))
  Median[i,]<-apply(VorList[[i]],2,median,na.rm=T)
  Mean[i,]<-apply(VorList[[i]],2,mean,na.rm=T)
  Upper[i,]<-apply(VorList[[i]],2,quantile,probs=c(.975),na.rm=T)
  Lower[i,]<-apply(VorList[[i]],2,quantile,probs=c(.025),na.rm=T)
  
  # update progress bar
  setTxtProgressBar(pb, i)

}
output<-list(Conf,Median,Mean,Upper,Lower)
return(output)
}


RecalcMAF<-function(FlowStats){
  #Calculate MAF
  for(i in 2:5){
    FlowStats[[i]]<-cbind(FlowStats[[i]][,1:17],MAF=apply(FlowStats[[i]][,1:17],1,DailyMeanFDC))
  }
  
  #ReCalculate Confidence Intervals
  FlowStats[[1]]<-(FlowStats[[4]]-FlowStats[[5]])/FlowStats[[2]]
  return(FlowStats)
}

CalcStatsDF<-function(Estimate,Actual){
  Stats<-data.frame()
  for(i in 1:ncol(Estimate)){
    tmp<-CalcStats(Estimate[,i],Actual[,i])
    Stats<-rbind(Stats,tmp)
  }
  names(Stats)<-c("RMSE","RRMSE","Bias","NASH")
  return(Stats)
}
  

