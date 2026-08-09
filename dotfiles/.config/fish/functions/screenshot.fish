function screenshot --description 'Take an interactive screenshot'
    screencapture -i "$HOME/Desktop/screenshot-"(date +%Y%m%d-%H%M%S)".png"
end
