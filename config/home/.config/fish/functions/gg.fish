function gg
	git grep $argv
	if test $status = 128
		rg $argv
	end
end
