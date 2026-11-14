function gh-token-save-shared --description 'Save the GitHub CLI token in Kinko shared scope'
    if not type -q kinko
        echo "Error: kinko is not installed." >&2
        return 1
    end

    set -l token (env GITHUB_TOKEN= gh auth token 2>/dev/null)
    if test -z "$token"
        echo "Error: Failed to get GitHub token. Run 'gh auth login' first." >&2
        return 1
    end

    kinko set-key GITHUB_TOKEN --shared --value "$token"
    or begin
        echo "Error: Failed to save GITHUB_TOKEN to Kinko shared scope." >&2
        return 1
    end

    set -gx GITHUB_TOKEN $token
    echo "Saved GITHUB_TOKEN to Kinko shared scope"
    echo "GITHUB_TOKEN exported to current session"
end
