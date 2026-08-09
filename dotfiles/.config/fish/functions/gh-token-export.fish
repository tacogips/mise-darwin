function gh-token-export --description 'Export the GitHub CLI token to this shell'
    set -l token (env GITHUB_TOKEN= gh auth token 2>/dev/null)
    if test -z "$token"
        echo "Error: Failed to get GitHub token. Run 'gh auth login' first." >&2
        return 1
    end

    set -gx GITHUB_TOKEN $token
    echo "GITHUB_TOKEN exported to current session"
end
