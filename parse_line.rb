
require_relative 'convert_dt'

def extract_values line, column_sizes
	result = []
	offset = 0
	for column_size in column_sizes do
		cell_value = line[offset..(offset + column_size)].strip
		if is_valid_dt cell_value
			cell_value = convertDT cell_value
		end
		result << cell_value
		offset += column_size + 1
	end
	return result
end