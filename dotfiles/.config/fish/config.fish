set -gx EDITOR nvim
set -gx LANG en_US.UTF-8
set -gx LC_ALL en_US.UTF-8
set -gx XDG_CACHE_HOME $HOME/.cache
set -gx XDG_CONFIG_HOME $HOME/.config
set -gx XDG_DATA_HOME $HOME/.local/share
set -gx XDG_BIN_HOME $HOME/.local/bin
set -gx DEVELOPER_DIR /Applications/Xcode.app/Contents/Developer
set -gx TOOLCHAINS com.apple.dt.toolchain.XcodeDefault
set -gx SDKROOT $DEVELOPER_DIR/Platforms/MacOSX.platform/Developer/SDKs/MacOSX.sdk

fish_add_path --prepend $HOME/.local/bin
fish_add_path --prepend $DEVELOPER_DIR/Toolchains/XcodeDefault.xctoolchain/usr/bin
fish_add_path --prepend /opt/homebrew/bin /usr/local/bin

set fish_greeting

if type -q mise
    mise activate fish | source
end

if type -q zoxide
    zoxide init fish --cmd cd | source
end

# Secrets remain outside Git. Kinko's shared scope is loaded only when present.
if status is-interactive; and type -q kinko
    kinko export fish --shared-only --force --confirm=false 2>/dev/null | source
end

alias brewup='brew update && brew upgrade'
alias o='open'
alias ll='eza --all --long --git --icons=auto'
alias cat='bat'
alias gs='git status'
alias gps='git push origin'
alias gpl='git pull origin'
alias ghb='gh browse'

bind -M insert ctrl-h backward-delete-char
bind -M insert ctrl-a beginning-of-line
