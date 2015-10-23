#############################
#
# 	libXML.R
#
# 	Author: 	Wayne Jenkinson 
#	Date:		2012-06-05 
#
#############################

library(XML)

xmlCoef <- function(coef.name, coef.value) {

	out.xml <- newXMLNode("statistic", newXMLNode("name", coef.name), newXMLNode("value", coef.value))
}

xmlHeader <- function(watershed.name, watershed.desc, sim.date.time){
	
	out.xml <- xmlNode("watershedModel")
	
	out.xml <- addChildren(out.xml, xmlNode("name", watershed.name))
	out.xml <- addChildren(out.xml, xmlNode("description", watershed.desc))
	out.xml <- addChildren(out.xml, xmlNode("sim_date_time", sim.date.time))
	out.xml <- addChildren(out.xml, xmlNode("eval_date_time", Sys.Date()))
	
}