# Utility function (to be used in irb) that allows looking at lines in tituly.txt and manually guess
# encoding mappings.
# This is because the encoding isn't really windows-1250...

def get_ords(string)
	string.each_char do |char|
		puts "#{char} > #{char.ord}"
	end
end

lines = []
File.open("pomocne/tituly.txt", "r", :encoding => 'windows-1250').each do |line|
	lines << line
end

