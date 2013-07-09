function rg
	if isatty stdout
		rgrep --color=always $argv .  | less -R -F -X -S
	else
		rgrep $argv .
	end
end
