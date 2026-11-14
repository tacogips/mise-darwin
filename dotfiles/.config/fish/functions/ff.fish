function ff
    set dest (fd --color=never $argv[1] | fzf +m --query "$LBUFFER" --prompt="find > ")
    if test -n "$dest"
        zed "$dest"
    end
end
