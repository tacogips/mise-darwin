function cdp
    # cd to path from clipboard
    # On Darwin, use pbpaste; on Linux, use wl-paste
    if type -q pbpaste
        cd (pbpaste)
    else if type -q wl-paste
        cd (wl-paste -n)
    end
end
