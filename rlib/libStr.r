#
# String Library (libStr.r)
#
# A list of functions used for string processing


Trim <- function (x) { #trim leading and trailing spaces
	  
	x.trim <- sub("(^\\s+)|(\\s+$)", "",x)  #leading and trailing whitespace "\\s+"
	x.trim
}

Quotes <- function(x){
  # add quotes to a string
  # x - input character string
  x.out <- paste("\"", x, "\"", sep="")
}
  
  