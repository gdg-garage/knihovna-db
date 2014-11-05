# encoding: utf-8

require 'csv'
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

column_names_line = nil
column_names = nil
column_sizes = nil
printed_header = false

error_count = 0

CSV do |csv|
	File.open(filename, "r", :encoding => 'windows-1250').each do |line|
		next if /^Records affected/ =~ line  # Last line in database export.

		if /^\s*$/ =~ line then
			# Blank line.
			column_sizes = nil
			column_names_line = nil
			next
		end

		if /^[=\s]+$/ =~ line then  # Underscore line.
			next if column_sizes != nil
			column_sizes = get_column_widths line
			column_names = extract_values column_names_line, column_sizes
			if not printed_header then
				csv << column_names
				printed_header = true
			end
			next
		end

		next if line == column_names_line

		if column_sizes != nil then
			begin
				csv_values = extract_values line.encode("utf-8"), column_sizes
				csv << csv_values
			rescue
				error_count += 1
				$stderr.puts line
				# Process.exit(3)
			end
		else
			column_names_line = line
		end
	end
end

$stderr.puts "Number of encoding errors: #{error_count}." 