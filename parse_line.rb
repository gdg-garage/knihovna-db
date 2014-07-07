


column_sizes = [19, 16, 25, 13, 20]
line = "            2658187           113577  7-JAN-2008 17:52:09.0000             5                  333 "



def extract_values line, column_sizes
	result = []
	offset = 0
	for column_size in column_sizes do
		result << line[offset..(offset + column_size)].strip
		offset += column_size + 1
	end
	return result
end

puts extract_values line, column_sizes