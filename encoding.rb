# encoding: utf-8
char_map=[[230,"Š"],[160,"á"],[236,"ý"],
	[133,"ů"],[159,"č"],[161,"í"],
	[130,"é"],[216,"ě"],[253,"ř"], 
	[156,"ť"],[144,"É"],[231,"š"],
	[160,"á"]]

pangram = "Příliš žluťoučký kůň úpěl ďábelské ódy"

def convert_to_utf8(string)
	string.each_char do |char|
		puts char.ord
	end
end

convert_to_utf8("a")