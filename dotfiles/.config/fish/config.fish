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
alias f='command fd'

set fish_cursor_default block
set fish_cursor_insert line
set fish_cursor_visual underscore
set fish_cursor_replace_one underscore

fish_vi_key_bindings
bind -M insert ctrl-p up-or-search
bind -M insert ctrl-n down-or-search
bind -M insert ctrl-o accept-autosuggestion
bind -M insert ctrl-h backward-delete-char
bind -M insert ctrl-a beginning-of-line

function __taco_fish_bind_mode_indicator
    switch $fish_bind_mode
        case default
            set_color --bold red
            echo -n '[N] '
        case insert
            set_color --bold green
            echo -n '[I] '
        case replace_one
            set_color --bold green
            echo -n '[R] '
        case visual
            set_color --bold magenta
            echo -n '[V] '
    end
    set_color normal
end

function fish_mode_prompt
end

set -g fish_escape_delay_ms 10
set -g __fish_git_prompt_show_informative_status true
set -g __fish_git_prompt_showdirtystate true
set -g __fish_git_prompt_showstagedstate true
set -g __fish_git_prompt_showuntrackedfiles true
set -g __fish_git_prompt_showupstream informative
set -g __fish_git_prompt_showcolorhints true

function fish_prompt
    set -l last_status $status
    __taco_fish_bind_mode_indicator
    set_color $fish_color_cwd
    echo -n (prompt_pwd)
    set_color normal

    set -l git_info (fish_vcs_prompt " (%s)")
    if test -n "$git_info"
        echo -n $git_info
    end

    if test $last_status -ne 0
        set_color red
        echo -n " [$last_status]"
        set_color normal
    end

    echo
    if fish_is_root_user
        echo -n '# '
    else
        echo -n '> '
    end
end

function __taco_warn_if_kinko_locked
    if not command -sq kinko
        return
    end
    set -l kinko_status (kinko status 2>/dev/null | string trim)
    if test "$kinko_status" = locked
        echo
        set_color --bold red
        echo '!!! KINKO IS LOCKED !!!'
        set_color --bold yellow
        echo "Run 'kinko unlock' if you need shared secrets."
        set_color normal
    end
end

function __taco_warn_if_kinko_locked_on_pwd_change --on-variable PWD
    __taco_warn_if_kinko_locked
end

set -l exports_file "$HOME/.config/fish/exports.fish"
if test -f $exports_file
    source $exports_file
end

if status is-interactive
    __taco_warn_if_kinko_locked
end
