# Utility function (to be used in irb) that allows looking at lines in tituly.txt and manually guess
# encoding mappings.
# This is because the encoding isn't really windows-1250...

def get_ords(string)
	string.each_char do |char|
		puts "#{char} > #{char.ord}"
	end
end

def find_in_lines(lines, regexp, offset)
	lines.each do |line|
		if regexp =~ line then
			offset -= 1
			if offset == 0 then
				get_ords(line)
			  break
			end
			puts line
		end
	end
end

@lines = []
File.open("pomocne/tituly.txt", "r", :encoding => 'ibm852').each do |line|
	@lines << line
end