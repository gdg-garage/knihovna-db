# puvodni format: 7-JAN-2008 17:51:51.0000
# novy format (ISO 8601, UTC +0): 2014-07-21T09:10:37Z
# MLP_dt_test = "7-JAN-2014 09:51:51.0000"

require 'time'
require 'date'

def is_valid_dt(string):
	return false

def convertDT(mlp_dt)

	mlp_dt = "#{mlp_dt.strip} #{Time.now.zone}"

	t_obj = DateTime.parse(mlp_dt)
	
	return t_obj.iso8601(0)
end
