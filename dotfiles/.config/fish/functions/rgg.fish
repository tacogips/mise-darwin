function rgg
    set dest (rg --line-number --no-heading --color=never $argv[1] | fzf +m --query "$LBUFFER" --prompt="rg > ")
    if test -n "$dest"
        set line_number (echo $dest | cut -d: -f2)
        set file_path (echo $dest | cut -d: -f1)
        nvim "+$line_number" "$file_path"
    end
end
