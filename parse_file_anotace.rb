# encoding: utf-8

# This file is a special case for 'anotace.txt' (or any other similar file) which has its
# rows completely screwed up.

require 'csv'
require_relative 'parse_line'
require_relative 'get_column_widths'

filename = ARGV[0]

if filename == nil then
	puts "Usage: ruby parse_file_anotace.rb filename.txt."
	Process.exit(1)
end

if not File.file?(filename) then
	puts "Filename '#{filename}' doesn't seem to exist or is not a file."
	Process.exit(2)
end

# Ran `cat pomocne/anotace.txt | grep -e "TITUL_KEY" | sort -u`
# to make sure that all headers are exactly the same.

column_names = [
	"TITUL_KEY", "ANOTACE_TXANOTACE", "ANOTACE_DLOUHA"
]
column_sizes = []
printed_header = false
last_row_closed = true
last_key = nil
last_text_short = nil
last_text_long = nil

csv_values = nil
error_count = 0

def add_stray_line line, csv_values
	if csv_values.length == 2 then
		csv_values << line.encode("utf-8")
	elsif csv_values.length == 3 then
		csv_values[2] << line.encode("utf-8")
	else
		raise "Bad state"
	end
end

def sanitize_string s
	s.gsub!(/<null>/, '')
	s.strip!
end

def sanitize_values csv_values
	sanitize_string csv_values[1]
	sanitize_string csv_values[2]
end

def save_to_csv csv_values, csv
	if csv_values.length == 2 then
		csv_values << ""
	end
	sanitize_values csv_values
	csv << csv_values
end

CSV do |csv|
	File.open(filename, "r", :encoding => 'windows-1250').each do |line|
		next if /^Records affected/ =~ line  # Last line in database export.

		if /^\s*$/ =~ line then
			# Blank line.
			next
		end

		if /^[A-Z_\s]+$/ =~ line then  # Header line.
			unless line.include? column_names[0] and line.include? column_names[1] and line.include? column_names[2] then
				# Looked like header line but isn't.
				add_stray_line line, csv_values if not last_row_closed
				next
			end
			save_to_csv csv_values, csv if not last_row_closed
			last_row_closed = true
			next
		end

		if /^[=\s]+$/ =~ line then  # Underscore line.
			save_to_csv csv_values, csv if not last_row_closed
			last_row_closed = true
			next
		end

		item_id_candidate = line[0..12].strip
		if /^[\s\d]+$/ =~ item_id_candidate and line.length > 13 then
			item_id = nil
			begin
				item_id = Integer(item_id_candidate)
			rescue
				if not last_row_closed then
					add_stray_line line, csv_values
					next
				else
					raise "We encountered a totally stray line here: #{line}"
				end
			end
			save_to_csv csv_values, csv if not last_row_closed
			csv_values = [item_id]
			csv_values << line[13..(13+250)].encode("utf-8")
			csv_values << line[(13+250)..-1].encode("utf-8") if line.length > 13+250
			last_row_closed = false
			next
		end

		add_stray_line line, csv_values if not last_row_closed
	end
end

$stderr.puts "Number of encoding errors: #{error_count}." 