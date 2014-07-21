# puvodni format: 7-JAN-2008 17:51:51.0000
# novy format (ISO 8601, UTC +0): 2014-07-21T09:10:37Z
# strftime, datetime.new
# posun casu

MLP_dt_test = "7-JAN-2008 17:51:51.0000"

def convertDT(mlp_dt)
	mlp_dt = mlp_dt.strip

	month_of_year = Array.new(12)
	month_of_year = ["JAN","FEB","MAR","APR","MAY","JUN","JUL","AUG","SEP","OCT","NOV","DEC"]	
	datum = mlp_dt.split(" ").first
	time =  mlp_dt.split(" ").last
	
	datum_split = datum.split("-") 
	time_split = time.split(".")
	mesic = (month_of_year.index(datum_split[1]) + 1).to_s.rjust(2, '0')
	return "#{datum_split.last}-#{mesic}-#{datum_split.first}T#{time_split.first}Z"
end

upraveno = convertDT(MLP_dt_test)
puts upraveno
