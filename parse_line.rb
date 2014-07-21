
def extract_values line, column_sizes
	result = []
	offset = 0
	for column_size in column_sizes do
		result << line[offset..(offset + column_size)].strip
		offset += column_size + 1
	end
	return result
end