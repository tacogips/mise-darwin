function ppp
    # Copy current directory to clipboard
    # On Darwin, use pbcopy; on Linux, use wl-copy
    if type -q pbcopy
        pwd | pbcopy
    else if type -q wl-copy
        pwd | wl-copy
    end
end
