def extract_values line
	spaces = []
	result = []

	while result != nil do
		
		if spaces.length==0
			line=line[0,line.length]
		else	
			line=line[spaces.last+1,line.length]
		end

		result = line.index(' ')
		spaces.push(result)
	end	
	
	return spaces
end