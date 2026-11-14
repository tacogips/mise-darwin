function hs
    set -l cmd (history | fzf --height 40% --layout reverse --info inline --border --tac)
    if test -n "$cmd"
        commandline -r $cmd
        commandline -f execute
    end
end
