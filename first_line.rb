filename = "vypujcky.txt"
lines = 200000

out = File.open("#{filename}.out.txt", "w")
File.open(filename, "r").each do |line|
  out.write line
  lines -= 1
  if lines <= 0 then
    break
  end
end

out.close
