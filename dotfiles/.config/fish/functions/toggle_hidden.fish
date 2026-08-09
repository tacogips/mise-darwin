function toggle_hidden --description 'Toggle hidden files in Finder'
    set -l current (defaults read com.apple.finder AppleShowAllFiles 2>/dev/null)
    if test "$current" = YES -o "$current" = 1
        defaults write com.apple.finder AppleShowAllFiles -bool false
    else
        defaults write com.apple.finder AppleShowAllFiles -bool true
    end
    killall Finder
end
