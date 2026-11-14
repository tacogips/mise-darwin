function fdd
    set dest (fd --type directory | fzf +m --query "$argv")
    if test -n "$dest"
        cd "$dest"
    end
end
