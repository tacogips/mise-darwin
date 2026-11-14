function gh-token-reset --description 'Remove GITHUB_TOKEN from this shell'
    set -e GITHUB_TOKEN
    echo "GITHUB_TOKEN unset from current session"
end
