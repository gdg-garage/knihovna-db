require_relative 'parse_line'
require_relative 'get_column_widths'

filename = ARGV[0]

if filename == nil then
	puts "Usage: ruby parse_file.rb filename.txt."
	Process.exit(1)
end

if not File.file?(filename) then
	puts "Filename '" + filename + "' doesn't seem to exist or is not a file."
	Process.exit(2)
end

MAX_LINES = 100
lines = 0

column_names_line = nil
column_names = nil
column_sizes = nil

File.open(filename, "r").each do |line|
	next if /^\s*$/ =~ line
	if /^[=\s]+$/ =~ line then
		next if column_sizes != nil
		column_sizes = get_column_widths line
		column_names = extract_values column_names_line, column_sizes
		next
	end

	if column_sizes != nil then
		puts extract_values line, column_sizes
	else
		column_names_line = line
	end

  lines += 1
  if lines >= MAX_LINES then
    break
  end
end

puts column_names_line
puts column_names
puts column_sizes

column_sizes = [19, 16, 25, 13, 20]
line = "            2658187           113577  7-JAN-2008 17:52:09.0000             5                  333 "



#puts extract_values line, column_sizes