function fd
    set -l selected_dir (zoxide query --list --score | fzf --height 40% --layout reverse --info inline --border --preview "eza --all --group-directories-first --header --long --no-user --no-permissions --color=always {2}" --no-sort | awk '{print $2}')
    if test -n "$selected_dir"
        cd $selected_dir
    end
end
