function ql --description 'Open files with Quick Look'
    qlmanage -p $argv >/dev/null 2>&1 &
end
